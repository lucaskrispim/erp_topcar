from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Ledger, Installment, FinancialAccount

def settle_ledger(ledger_id, amount, account_id, user, payment_method='TRANSFER'):
    """
    Realiza a baixa (pagamento/recebimento) de um lançamento.
    1. Cria a Parcela (Installment) confirmando o fluxo.
    2. Atualiza o Saldo da Conta Bancária.
    3. Atualiza o Status do Lançamento (Ledger).
    """
    with transaction.atomic():
        # 1. Busca e Trava os registros
        ledger = Ledger.objects.select_for_update().get(id=ledger_id)
        account = FinancialAccount.objects.select_for_update().get(id=account_id)

        if ledger.status in ['PAID', 'CANCELED']:
            raise ValidationError("Este lançamento já está quitado ou cancelado.")

        # --- TRAVA DE SALDO (NOVO) ---
        # Se for PAGAMENTO (Dinheiro saindo) e não tiver saldo...
        if ledger.transaction_type == 'PAYABLE':
            if account.balance < amount:
                raise ValidationError(f"Saldo insuficiente em '{account.name}'. Disponível: R$ {account.balance}, Necessário: R$ {amount}")

        # 2. Cria o registro do movimento financeiro (O Recibo)
        # Calcula o número da parcela (se já tiver parciais, soma 1)
        next_num = ledger.parcelas.count() + 1
        
        Installment.objects.create(
            ledger=ledger,
            financial_account=account,
            installment_number=next_num,
            due_date=timezone.now().date(),
            pay_date=timezone.now().date(), # Data real do pagamento
            value=amount,     # Valor original previsto (simplificado)
            paid_value=amount, # Valor efetivamente pago
            payment_method=payment_method,
            loja_id=ledger.loja_id,
            created_by=user
        )

        # 3. Atualiza Saldo da Conta
        if ledger.transaction_type == 'RECEIVABLE':
            account.balance += amount # Dinheiro entra
        else:
            account.balance -= amount # Dinheiro sai
        account.save()

        # 4. Atualiza Status do Lançamento Pai
        # Verifica se quitou tudo (Total - Pago)
        total_pago = sum(p.paid_value for p in ledger.parcelas.all())
        
        if total_pago >= ledger.total_value:
            ledger.status = 'PAID'
        else:
            ledger.status = 'PARTIAL'
        
        ledger.save()

    return ledger