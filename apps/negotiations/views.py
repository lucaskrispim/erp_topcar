from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction

from .forms import SaleForm
from .models import NegotiationItem
from .services import approve_negotiation

from django.shortcuts import render, redirect, get_object_or_404
from .models import Negotiation

@login_required
def negotiation_create(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Cria o Cabeçalho (Rascunho)
                    negotiation = form.save(commit=False)
                    negotiation.negotiation_type = 'SALE'
                    negotiation.status = 'DRAFT'
                    negotiation.loja_id = 1 # Default
                    negotiation.created_by = request.user
                    negotiation.save()

                    # 2. Cria o Item (O Carro saindo)
                    vehicle = form.cleaned_data['vehicle']
                    price = form.cleaned_data['sale_value']
                    
                    NegotiationItem.objects.create(
                        negotiation=negotiation,
                        vehicle=vehicle,
                        flow='OUT', # Saída de Estoque
                        agreed_value=price,
                        loja_id=1,
                        created_by=request.user
                    )

                    # 3. Aprova e Gera Financeiro (A Mágica)
                    approve_negotiation(negotiation.id, request.user)
                    
                    messages.success(request, f"Venda #{negotiation.id} realizada com sucesso! Estoque baixado e Financeiro gerado.")
                    return redirect('dashboard') # Ou para uma lista de vendas
            
            except Exception as e:
                messages.error(request, f"Erro ao processar venda: {str(e)}")
    else:
        form = SaleForm()

    return render(request, 'negotiations/negotiation_form.html', {'form': form})


@login_required
def negotiation_list(request):
    # Lista ordenando da mais recente para a mais antiga
    sales = Negotiation.objects.filter(negotiation_type='SALE').select_related(
        'customer', 'seller'
    ).prefetch_related('items__vehicle').order_by('-created_at')
    
    return render(request, 'negotiations/negotiation_list.html', {'sales': sales})

@login_required
def negotiation_detail(request, pk):
    # Busca a venda e seus itens + financeiro atrelado
    sale = get_object_or_404(Negotiation, pk=pk)
    
    # Busca os lançamentos financeiros gerados por essa venda
    # (Lembra do campo 'negotiation' que descomentamos no Ledger?)
    financials = sale.ledger_set.all() 

    return render(request, 'negotiations/negotiation_detail.html', {
        'sale': sale,
        'financials': financials
    })