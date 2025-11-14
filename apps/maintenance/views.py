from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

from .models import ServiceOrder, ServiceOrderItem
from .forms import ServiceOrderCreateForm, ServiceOrderItemForm
from .services import complete_service_order

@login_required
def maintenance_list(request):
    # Lista OS ordenadas pela mais recente
    orders = ServiceOrder.objects.select_related('vehicle', 'supplier').order_by('-issue_date')
    return render(request, 'maintenance/maintenance_list.html', {'orders': orders})

@login_required
def maintenance_create(request):
    if request.method == 'POST':
        form = ServiceOrderCreateForm(request.POST)
        if form.is_valid():
            os = form.save(commit=False)
            os.created_by = request.user
            os.status = 'APPROVED' # Já nasce aprovada/em execução
            os.save()
            
            # Atualiza status do carro para OFICINA
            os.vehicle.status = 'MAINTENANCE'
            os.vehicle.save()
            
            messages.success(request, f"OS #{os.id} aberta com sucesso! Agora adicione os itens.")
            return redirect('maintenance_detail', pk=os.id)
    else:
        form = ServiceOrderCreateForm()
    return render(request, 'maintenance/maintenance_form.html', {'form': form})

@login_required
def maintenance_detail(request, pk):
    os = get_object_or_404(ServiceOrder, pk=pk)
    items = os.items.all()
    
    # Calcula total parcial na tela (antes de fechar)
    total_atual = items.aggregate(Sum('cost'))['cost__sum'] or 0
    
    # Formulário de Adicionar Item (Só aparece se não estiver concluída)
    form_item = ServiceOrderItemForm()
    
    return render(request, 'maintenance/maintenance_detail.html', {
        'os': os,
        'items': items,
        'total_atual': total_atual,
        'form_item': form_item
    })

@login_required
def maintenance_add_item(request, pk):
    """ View exclusiva para processar o POST de adicionar item """
    os = get_object_or_404(ServiceOrder, pk=pk)
    
    if os.status == 'COMPLETED':
        messages.error(request, "Esta OS já está fechada.")
        return redirect('maintenance_detail', pk=pk)

    if request.method == 'POST':
        form = ServiceOrderItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.service_order = os
            item.created_by = request.user
            item.save()
            messages.success(request, "Item adicionado.")
        else:
            messages.error(request, "Erro ao adicionar item. Verifique os dados.")
            
    return redirect('maintenance_detail', pk=pk)

@login_required
def maintenance_finish(request, pk):
    """ Chama o Serviço que fecha a OS e gera a dívida """
    try:
        complete_service_order(pk, request.user)
        messages.success(request, "OS Concluída! Contas a Pagar gerado e Veículo liberado.")
    except Exception as e:
        messages.error(request, f"Erro ao concluir: {str(e)}")
        
    return redirect('maintenance_detail', pk=pk)