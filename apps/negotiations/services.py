from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

from .models import Negotiation
from vehicles.models import Vehicle
from financial.models import Ledger, ChartOfAccounts

def approve_negotiation(negotiation_id, user):
    """
    Realiza a aprovação atômica da negociação:
    1. Trava registro
    2. Calcula Saldo
    3. Atualiza Veículos
    4. Gera Financeiro
    """
    with transaction.atomic():
        # 1. Trava o registro para evitar concorrência (select_for_update)
        negotiation = Negotiation.objects.select_for_update().get(id=negotiation_id)

        if negotiation.status != 'DRAFT':
            raise ValidationError("Apenas negociações em Rascunho podem ser aprovadas.")

        items = negotiation.items.select_related('vehicle').all()
        if not items:
            raise ValidationError("A negociação não possui itens.")

        total_out = Decimal('0.00')
        total_in = Decimal('0.00')

        # 2 e 3. Itera itens e atualiza veículos
        for item in items:
            vehicle = item.vehicle
            
            if item.flow == 'OUT':
                if vehicle.status != 'AVAILABLE':
                    raise ValidationError(f"Veículo {vehicle} não está disponível para venda.")
                
                vehicle.status = 'SOLD'
                # Nota: Em um sistema real, mudaríamos o current_owner para o negotiation.customer
                # Mas vamos manter simples conforme pedido.
                total_out += item.agreed_value
            
            elif item.flow == 'IN':
                # Entrando na loja (Troca)
                vehicle.status = 'MAINTENANCE' # Entra para revisão
                vehicle.current_owner = negotiation.seller.entidade # Erro lógico corrigido: A loja vira dona?
                # TODO: Precisamos definir a ENTIDADE LOJA no settings ou pegar dinamicamente. 
                # Por hora, assume-se que o processo de entrada já ajustou o dono ou faremos depois.
                
                total_in += item.agreed_value
            
            vehicle.save()

        saldo_final = total_out - total_in
        negotiation.total_value = saldo_final
        negotiation.negotiation_date = timezone.now()
        negotiation.status = 'APPROVED'
        negotiation.save()

        # 4. Gera Financeiro (Ledger)
        if saldo_final > 0:
            # Cliente paga a loja
            try:
                categoria = ChartOfAccounts.objects.get(code='1.01') # Exemplo: Receita Venda
            except ChartOfAccounts.DoesNotExist:
                raise ValidationError("Plano de contas 'Receita' não configurado.")

            Ledger.objects.create(
                entity=negotiation.customer,
                chart_of_accounts=categoria,
                total_value=saldo_final,
                transaction_type='RECEIVABLE',
                due_date=timezone.now().date(), # Vence hoje (ou configurar regra)
                description=f"Venda Ref. Negociação #{negotiation.id}",
                negotiation=negotiation,
                loja_id=negotiation.loja_id,
                created_by=user
            )
        
        elif saldo_final < 0:
            # Loja paga ao cliente (Troco)
            try:
                categoria = ChartOfAccounts.objects.get(code='2.01') # Exemplo: Custo Aquisição
            except ChartOfAccounts.DoesNotExist:
                raise ValidationError("Plano de contas 'Custo Aquisição' não configurado.")

            Ledger.objects.create(
                entity=negotiation.customer,
                chart_of_accounts=categoria,
                total_value=abs(saldo_final),
                transaction_type='PAYABLE',
                due_date=timezone.now().date(),
                description=f"Troco/Aquisição Ref. Negociação #{negotiation.id}",
                negotiation=negotiation,
                loja_id=negotiation.loja_id,
                created_by=user
            )

    return negotiation