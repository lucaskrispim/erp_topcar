from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

from .models import ServiceOrder
from financial.models import Ledger, ChartOfAccounts

def complete_service_order(service_order_id, user):
    """
    1. Calcula total da OS.
    2. Atualiza status da OS.
    3. Gera contas a pagar (Ledger) para o Fornecedor.
    """
    with transaction.atomic():
        # Trava registro
        os = ServiceOrder.objects.select_for_update().get(id=service_order_id)

        if os.status == 'COMPLETED':
            raise ValidationError("Esta OS já foi concluída.")
        
        # Calcula total
        items = os.items.all()
        if not items.exists():
            raise ValidationError("Não é possível concluir uma OS sem itens.")
            
        total_val = sum(item.cost for item in items)
        os.total_cost = total_val
        os.completion_date = timezone.now().date()
        os.status = 'COMPLETED'
        os.save()

        # Busca Categoria Financeira (Assumindo que criaremos o código 3.01)
        try:
            # Tenta buscar uma conta de despesa de manutenção
            categoria = ChartOfAccounts.objects.get(code='3.01') 
        except ChartOfAccounts.DoesNotExist:
            # Fallback ou erro
            raise ValidationError("Plano de contas '3.01 - Manutenção' não encontrado.")

        # Cria o Passivo (Dívida com o Mecânico)
        Ledger.objects.create(
            entity=os.supplier, # Devemos para o Mecânico Zé
            chart_of_accounts=categoria,
            total_value=total_val,
            transaction_type='PAYABLE',
            status='OPEN',
            due_date=timezone.now().date(), # Vence hoje (ou regra de +30 dias)
            description=f"Ref. OS #{os.id} - Manutenção {os.vehicle}",
            vehicle=os.vehicle, # O ÂNCORA DO CUSTO REAL
            loja_id=os.loja_id,
            created_by=user
        )

    return os