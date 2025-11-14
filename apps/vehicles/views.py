from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q
from .forms import VehicleAcquisitionForm
from .services import register_vehicle_acquisition
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect, get_object_or_404 
from .forms import VehicleAcquisitionForm, VehicleEditForm
from django.db.models import Q, ProtectedError # <--- VERIFIQUE ESTE IMPORT

from django.db.models import Sum, F, DecimalField, Value
from django.db.models.functions import Coalesce
from .models import Vehicle, Brand, Model
from .models import Brand # Importe o modelo Brand
from .forms import BrandForm # Importe o novo formulário

# ... (imports anteriores: Q, ProtectedError, etc.) ...
from .forms import ModelForm # Importe o novo formulário


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

@login_required
def load_models(request):
    """
    View que o HTMX chama para carregar os modelos de uma marca.
    """
    # Pega o ID da marca que o HTMX enviou via GET
    brand_id = request.GET.get('brand') 
    
    # Filtra os modelos daquela marca
    models = Model.objects.filter(brand_id=brand_id).order_by('name')
    
    # Renderiza APENAS o HTML dos <option>
    return render(request, 'vehicles/partials/model_options.html', {'models': models})

# ... (Mantenha todas as views anteriores: vehicle_list, load_models, etc.) ...

# --- CRUD DE MARCAS ---

@login_required
def brand_list(request):
    brands = Brand.objects.all().order_by('name')
    return render(request, 'vehicles/brand_list.html', {'brands': brands})

@login_required
def brand_create(request):
    if request.method == 'POST':
        form = BrandForm(request.POST)
        if form.is_valid():
            brand = form.save(commit=False)
            brand.created_by = request.user
            brand.save()
            messages.success(request, f"Marca '{brand.name}' criada com sucesso.")
            return redirect('brand_list')
    else:
        form = BrandForm()
    return render(request, 'vehicles/brand_form.html', {'form': form, 'action': 'Nova'})

@login_required
def brand_update(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        form = BrandForm(request.POST, instance=brand)
        if form.is_valid():
            form.save()
            messages.success(request, f"Marca '{brand.name}' atualizada.")
            return redirect('brand_list')
    else:
        form = BrandForm(instance=brand)
    return render(request, 'vehicles/brand_form.html', {'form': form, 'action': 'Editar'})

@login_required
def brand_delete(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        try:
            brand_name = brand.name
            brand.delete()
            messages.success(request, f"Marca '{brand_name}' excluída com sucesso.")
        except ProtectedError:
            # TRAVA DE SEGURANÇA: Impede excluir se houver Modelos vinculados
            messages.error(request, f"Erro: A marca '{brand.name}' não pode ser excluída pois possui modelos de veículos vinculados a ela.")
    
    return redirect('brand_list')

# ... (Mantenha todas as views anteriores: brand_list, etc.) ...

# --- CRUD DE MODELOS ---

@login_required
def model_list(request):
    # Usamos select_related('brand') para otimizar a query (evitar N+1)
    models = Model.objects.select_related('brand').all().order_by('brand__name', 'name')
    return render(request, 'vehicles/model_list.html', {'models': models})

@login_required
def model_create(request):
    if request.method == 'POST':
        form = ModelForm(request.POST)
        if form.is_valid():
            model = form.save(commit=False)
            model.created_by = request.user
            model.save()
            messages.success(request, f"Modelo '{model.name}' criado com sucesso.")
            return redirect('model_list')
    else:
        form = ModelForm()
    return render(request, 'vehicles/model_form.html', {'form': form, 'action': 'Novo'})

@login_required
def model_update(request, pk):
    model = get_object_or_404(Model, pk=pk)
    if request.method == 'POST':
        form = ModelForm(request.POST, instance=model)
        if form.is_valid():
            form.save()
            messages.success(request, f"Modelo '{model.name}' atualizado.")
            return redirect('model_list')
    else:
        form = ModelForm(instance=model)
    return render(request, 'vehicles/model_form.html', {'form': form, 'action': 'Editar'})

@login_required
def model_delete(request, pk):
    model = get_object_or_404(Model, pk=pk)
    if request.method == 'POST':
        try:
            model_name = model.name
            model.delete()
            messages.success(request, f"Modelo '{model_name}' excluído com sucesso.")
        except ProtectedError:
            # TRAVA DE SEGURANÇA: Impede excluir se houver Veículos vinculados
            messages.error(request, f"Erro: O modelo '{model.name}' não pode ser excluído pois existem veículos cadastrados com ele.")
    
    return redirect('model_list')