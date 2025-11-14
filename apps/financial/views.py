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

# ... (imports anteriores: render, redirect, messages, etc.) ...
from .forms import ManualLedgerForm

# ... (imports anteriores: render, redirect, messages, etc.) ...
from django.db.models import ProtectedError # Importar para a lógica de exclusão
from .models import ChartOfAccounts # Importar o modelo
from .forms import ChartOfAccountsForm # Importar o formulário

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


# ... (Mantenha 'financial_list' e 'financial_statement') ...

@login_required
def ledger_manual_create(request):
    if request.method == 'POST':
        form = ManualLedgerForm(request.POST)
        if form.is_valid():
            ledger = form.save(commit=False)
            ledger.created_by = request.user
            ledger.status = 'OPEN' # Nasce em aberto
            ledger.save()
            messages.success(request, "Lançamento manual criado com sucesso.")
            return redirect('financial_list')
    else:
        form = ManualLedgerForm()

    return render(request, 'financial/ledger_manual_form.html', {'form': form})

# ... (Mantenha todas as views anteriores: financial_list, ledger_manual_create, etc.) ...

# --- CRUD DE PLANO DE CONTAS ---

@login_required
def chart_of_accounts_list(request):
    # Usa select_related para otimizar o carregamento da Conta Pai
    accounts = ChartOfAccounts.objects.select_related('parent').all().order_by('code')
    return render(request, 'financial/chart_of_accounts_list.html', {'accounts': accounts})

@login_required
def chart_of_accounts_create(request):
    if request.method == 'POST':
        form = ChartOfAccountsForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.created_by = request.user
            account.save()
            messages.success(request, f"Categoria '{account.name}' ({account.code}) criada com sucesso.")
            return redirect('chart_of_accounts_list')
    else:
        form = ChartOfAccountsForm()
    return render(request, 'financial/chart_of_accounts_form.html', {'form': form, 'action': 'Nova'})

@login_required
def chart_of_accounts_update(request, pk):
    account = get_object_or_404(ChartOfAccounts, pk=pk)
    if request.method == 'POST':
        form = ChartOfAccountsForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(request, f"Categoria '{account.name}' ({account.code}) atualizada.")
            return redirect('chart_of_accounts_list')
    else:
        form = ChartOfAccountsForm(instance=account)
    return render(request, 'financial/chart_of_accounts_form.html', {'form': form, 'action': 'Editar'})

@login_required
def chart_of_accounts_delete(request, pk):
    account = get_object_or_404(ChartOfAccounts, pk=pk)
    if request.method == 'POST':
        try:
            account_name = account.name
            account.delete()
            messages.success(request, f"Categoria '{account_name}' excluída com sucesso.")
        except ProtectedError:
            # Trava de segurança: impede excluir se houver Lançamentos ou Contas Filhas vinculadas
            messages.error(request, f"Erro: A categoria '{account.name}' não pode ser excluída. Ela está vinculada a Lançamentos ou é Conta Pai de outras categorias.")
    
    return redirect('chart_of_accounts_list')