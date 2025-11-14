from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q
from .models import Vehicle
from .forms import VehicleAcquisitionForm
from .services import register_vehicle_acquisition
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect, get_object_or_404 
from .forms import VehicleAcquisitionForm, VehicleEditForm
from django.db.models import Q, ProtectedError # <--- VERIFIQUE ESTE IMPORT

from django.db.models import Sum, F, DecimalField, Value
from django.db.models.functions import Coalesce

# --- VIEW 1: Listagem (Passo 7 - HTMX) ---
@login_required
def vehicle_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')

    # Otimização: select_related para evitar N+1 queries
    vehicles = Vehicle.objects.all().select_related('model', 'model__brand', 'current_owner')

    if query:
        vehicles = vehicles.filter(
            Q(model__name__icontains=query) | 
            Q(plate__icontains=query) |
            Q(chassi__icontains=query)
        )
    
    if status_filter:
        vehicles = vehicles.filter(status=status_filter)

    context = {
        'vehicles': vehicles,
        'status_choices': Vehicle.STATUS_CHOICES,
    }

    # SE for HTMX (o usuário digitou algo na busca), retorna só as linhas da tabela
    if request.headers.get('HX-Request'):
        return render(request, 'vehicles/partials/vehicle_table_rows.html', context)
    
    # SE for acesso normal, retorna a página completa
    return render(request, 'vehicles/vehicle_list.html', context)


# --- VIEW 2: Cadastro de Aquisição (Passo 8) ---
@login_required
def vehicle_create(request):
    if request.method == 'POST':
        form = VehicleAcquisitionForm(request.POST)
        if form.is_valid():
            try:
                # Extrai dados limpos
                vehicle_data = form.cleaned_data
                
                # Separa dados do vendedor (que não vão para o modelo Vehicle direto)
                seller_data = {
                    'name': vehicle_data.pop('seller_name'),
                    'document': vehicle_data.pop('seller_document')
                }
                
                # Chama o Serviço Atômico
                register_vehicle_acquisition(
                    vehicle_data=vehicle_data,
                    seller_data=seller_data,
                    user=request.user
                )
                
                messages.success(request, "Veículo adquirido e financeiro gerado com sucesso!")
                return redirect('vehicle_list') # Redireciona para a lista após salvar
            
            except Exception as e:
                messages.error(request, f"Erro ao registrar aquisição: {str(e)}")
    else:
        form = VehicleAcquisitionForm()

    return render(request, 'vehicles/vehicle_form.html', {'form': form})

@login_required
def vehicle_update(request, pk):
    # Busca o veículo pelo ID (pk) ou retorna 404
    vehicle = get_object_or_404(Vehicle, pk=pk)

    if request.method == 'POST':
        form = VehicleEditForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save() # Aqui podemos usar save direto pois não tem lógica financeira complexa na edição
            messages.success(request, f"Veículo {vehicle.plate or vehicle.model} atualizado com sucesso!")
            return redirect('vehicle_list')
    else:
        # Preenche o formulário com os dados atuais do banco
        form = VehicleEditForm(instance=vehicle)

    return render(request, 'vehicles/vehicle_edit.html', {
        'form': form,
        'vehicle': vehicle
    })


@login_required
def vehicle_delete(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)

    # Exige POST para evitar exclusão acidental por link
    if request.method == 'POST':
        try:
            placa_ou_modelo = vehicle.plate or vehicle.model
            vehicle.delete()
            messages.success(request, f"Veículo {placa_ou_modelo} excluído com sucesso.")
        except ProtectedError:
            # AQUI ESTÁ A SEGURANÇA DO ERP:
            # Se o carro tiver financeiro ou vendas atreladas, cai aqui.
            messages.error(request, "ERRO CRÍTICO: Não é possível excluir este veículo pois ele já possui Vendas, Manutenções ou Financeiro vinculados. Para tirá-lo de circulação, edite o status para 'Perda Total'.")
        except Exception as e:
            messages.error(request, f"Erro inesperado ao excluir: {str(e)}")
            
    return redirect('vehicle_list')


@login_required
def vehicle_roi_report(request):
    # 1. Busca apenas veículos vendidos
    # 2. Annotate: Cria uma coluna virtual 'total_maintenance' somando as OS do carro
    # 3. Coalesce: Se não tiver manutenção, considera 0.00 em vez de None (para não quebrar a conta)
    sold_vehicles = Vehicle.objects.filter(status='SOLD').annotate(
        total_maintenance=Coalesce(Sum('service_orders__total_cost'), Value(0, output_field=DecimalField()))
    ).annotate(
        # Agora podemos fazer a conta matemática direto no banco
        real_profit=F('sale_price') - F('acquisition_cost') - F('total_maintenance')
    ).order_by('-id')

    # Cálculo dos Totais Gerais para o Cabeçalho do Relatório
    totals = sold_vehicles.aggregate(
        sum_revenue=Sum('sale_price'),
        sum_acquisition=Sum('acquisition_cost'),
        sum_maintenance=Sum('total_maintenance'),
        sum_profit=Sum('real_profit')
    )

    return render(request, 'vehicles/roi_report.html', {
        'vehicles': sold_vehicles,
        'totals': totals
    })