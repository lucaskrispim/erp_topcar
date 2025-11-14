from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction

from .forms import SaleForm
from .models import NegotiationItem
from .services import approve_negotiation

from django.shortcuts import render, redirect, get_object_or_404
from .models import Negotiation

from vehicles.models import Vehicle, Brand, Model
from decimal import Decimal

from vehicles.models import Vehicle, Brand, Model # Importar modelos de veículos
from parties.models import Entity # Importar Entidade
from .services import approve_negotiation, cancel_negotiation
from django.core.exceptions import ValidationError


@login_required
def negotiation_create(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Cria a Negociação (Cabeçalho)
                    negotiation = form.save(commit=False)
                    negotiation.negotiation_type = 'SALE'
                    negotiation.status = 'DRAFT'
                    negotiation.created_by = request.user
                    negotiation.save()

                    # 2. Item 1: O Carro da Loja (SAÍDA)
                    vehicle_out = form.cleaned_data['vehicle']
                    price_out = form.cleaned_data['sale_value']
                    
                    NegotiationItem.objects.create(
                        negotiation=negotiation,
                        vehicle=vehicle_out,
                        flow='OUT',
                        agreed_value=price_out,
                        created_by=request.user
                    )

                    # 3. Item 2: A Troca (ENTRADA) - Se houver
                    if form.cleaned_data['has_trade_in']:
                        # A. Busca Marca/Modelo (Cria se não existir)
                        brand_name = form.cleaned_data['trade_in_brand_name']
                        model_name = form.cleaned_data['trade_in_model_name']
                        
                        brand_obj, _ = Brand.objects.get_or_create(name=brand_name.upper())
                        model_obj, _ = Model.objects.get_or_create(brand=brand_obj, name=model_name)
                        
                        # B. Pega o valor da troca (Custo de Aquisição)
                        value_in = form.cleaned_data['trade_in_value']

                        # C. Busca a Entidade da Loja (Dona do carro)
                        # Assumindo ID 1 para a Loja Matriz (Definido no script de seed)
                        loja_entity = Entity.objects.get(id=1) 
                        
                        # D. Cadastra o Veículo da Troca 100% Completo
                        vehicle_in = Vehicle.objects.create(
                            model=model_obj,
                            chassi=form.cleaned_data['trade_in_chassi'],
                            plate=form.cleaned_data['trade_in_plate'],
                            renavam=form.cleaned_data['trade_in_renavam'],
                            year_fab=form.cleaned_data['trade_in_year_fab'],
                            year_model=form.cleaned_data['trade_in_year_model'],
                            color=form.cleaned_data['trade_in_color'],
                            fuel_type=form.cleaned_data['trade_in_fuel_type'],
                            mileage=form.cleaned_data['trade_in_mileage'],
                            
                            status='MAINTENANCE', # Entra direto pra revisão
                            acquisition_cost=value_in, # O custo dele é quanto pagamos na troca!
                            sale_price=value_in * Decimal('1.3'), # Sugestão de preço (+30%)
                            
                            # O dono agora é a Loja, pois é uma aquisição.
                            current_owner=loja_entity, 
                            
                            created_by=request.user
                        )
                        
                        # E. Lança o Item na Negociação
                        NegotiationItem.objects.create(
                            negotiation=negotiation,
                            vehicle=vehicle_in,
                            flow='IN',
                            agreed_value=value_in,
                            created_by=request.user
                        )

                    # 4. Aprova tudo e gera financeiro (Saldo = Saída - Entrada)
                    # O service 'approve_negotiation' NÃO vai mudar o dono, 
                    # pois o carro já foi criado como dono da loja.
                    approve_negotiation(negotiation.id, request.user)
                    
                    messages.success(request, f"Venda #{negotiation.id} realizada! Financeiro gerado com sucesso.")
                    return redirect('negotiation_detail', pk=negotiation.id)
            
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


@login_required
def negotiation_cancel(request, pk):
    # Esta view só aceita POST (é uma Ação)
    if request.method == 'POST':
        try:
            cancel_negotiation(pk, request.user)
            messages.success(request, f"Negociação #{pk} cancelada com sucesso. Estoque e financeiro revertidos.")
        except ValidationError as e:
            # Captura erros de regra (Ex: "Já foi pago")
            msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            messages.error(request, msg)
        except Exception as e:
            messages.error(request, f"Erro técnico ao cancelar: {str(e)}")
            
    # Após cancelar (ou dar erro), volta para os detalhes
    return redirect('negotiation_detail', pk=pk)