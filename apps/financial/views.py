from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Ledger, FinancialAccount
from decimal import Decimal
from .services import settle_ledger
from django.core.exceptions import ValidationError

from django.db.models import Sum
from datetime import date, timedelta
from .models import Installment

@login_required
def financial_list(request):
    # Lista apenas o que está pendente
    ledgers = Ledger.objects.filter(status__in=['OPEN', 'PARTIAL']).order_by('due_date')
    accounts = FinancialAccount.objects.all()

    if request.method == 'POST':
        try:
            ledger_id = request.POST.get('ledger_id')
            
            # --- A CORREÇÃO ESTÁ AQUI ---
            # Pega o valor como string, troca vírgula por ponto (segurança extra)
            valor_raw = request.POST.get('amount').replace(',', '.')
            
            # Converte para Decimal (Dinheiro), NUNCA para float
            amount = Decimal(valor_raw)
            # ----------------------------
            
            account_id = request.POST.get('account_id')

            settle_ledger(
                ledger_id=ledger_id,
                amount=amount, # Agora estamos passando um Decimal
                account_id=account_id,
                user=request.user
            )
            messages.success(request, "Movimentação financeira registrada com sucesso!")
            return redirect('financial_list')
        # --- AQUI ESTÁ A MÁGICA DA MENSAGEM LIMPA ---
        except ValidationError as e:
            # Se o erro for de validação (regra de negócio), pegamos a mensagem limpa
            # e.messages[0] pega o texto sem os colchetes ['...']
            msg_erro = e.messages[0] if hasattr(e, 'messages') else str(e)
            messages.error(request, msg_erro)
            
        except Exception as e:
            # Se for um erro técnico (código quebrado), mostra o erro genérico
            messages.error(request, f"Erro técnico ao processar: {str(e)}")

    return render(request, 'financial/financial_list.html', {
        'ledgers': ledgers,
        'accounts': accounts
    })



@login_required
def financial_statement(request):
    # Filtros Padrão: Mês Atual
    today = date.today()
    first_day = today.replace(day=1)
    
    start_date = request.GET.get('start_date', first_day.isoformat())
    end_date = request.GET.get('end_date', today.isoformat())
    account_id = request.GET.get('account_id', '')

    # Base: Apenas parcelas PAGAS
    movements = Installment.objects.filter(
        pay_date__range=[start_date, end_date],
        paid_value__gt=0
    ).select_related('ledger', 'ledger__entity', 'financial_account').order_by('-pay_date', '-id')

    if account_id:
        movements = movements.filter(financial_account_id=account_id)

    # Totais do Período
    total_in = movements.filter(ledger__transaction_type='RECEIVABLE').aggregate(Sum('paid_value'))['paid_value__sum'] or 0
    total_out = movements.filter(ledger__transaction_type='PAYABLE').aggregate(Sum('paid_value'))['paid_value__sum'] or 0
    balance_period = total_in - total_out

    accounts = FinancialAccount.objects.all()

    return render(request, 'financial/financial_statement.html', {
        'movements': movements,
        'accounts': accounts,
        'total_in': total_in,
        'total_out': total_out,
        'balance_period': balance_period,
        # Devolvemos os filtros para o template manter preenchido
        'filter_start': start_date,
        'filter_end': end_date,
        'filter_account': int(account_id) if account_id else '',
    })