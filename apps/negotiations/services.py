from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

from .models import Negotiation
from vehicles.models import Vehicle
from financial.models import Ledger, ChartOfAccounts

from parties.models import Entity # Importar Entidade

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
            
        # Pega a entidade da Loja (ID 1 do script de seed)
        try:
            loja_entity = Entity.objects.get(id=1)
        except Entity.DoesNotExist:
             raise ValidationError("Entidade 'Loja Matriz' (ID 1) não encontrada. Execute o script de seed.")


        total_out = Decimal('0.00')
        total_in = Decimal('0.00')

        # 2 e 3. Itera itens e atualiza veículos
        for item in items:
            vehicle = item.vehicle
            
            if item.flow == 'OUT':
                if vehicle.status != 'AVAILABLE':
                    raise ValidationError(f"Veículo {vehicle} não está disponível para venda.")
                
                vehicle.status = 'SOLD'
                vehicle.current_owner = negotiation.customer # O cliente agora é o dono

                total_out += item.agreed_value
            
            elif item.flow == 'IN':
                # ATUALIZAÇÃO: O carro já foi criado na View como dono da loja
                # Aqui apenas confirmamos o status e o dono (redundância segura)
                vehicle.status = 'MAINTENANCE' 
                vehicle.current_owner = loja_entity

                total_in += item.agreed_value
            
            vehicle.save()

        # ... (O resto da função continua igual para calcular saldo e gerar Ledger) ...
        
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
                due_date=timezone.now().date(), 
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

@transaction.atomic
def cancel_negotiation(negotiation_id, user):
    """
    Reverte (Estorna) uma negociação aprovada.
    CORRIGIDO COM A ORDEM DE EXCLUSÃO CORRETA
    """
    negotiation = Negotiation.objects.select_for_update().get(id=negotiation_id)

    if negotiation.status == 'CANCELED':
        raise ValidationError("Esta negociação já está cancelada.")
        
    try:
        loja_entity = Entity.objects.get(id=1)
    except Entity.DoesNotExist:
         raise ValidationError("Entidade 'Loja Matriz' (ID 1) não encontrada.")

    # 1. Reverter Financeiro PRIMEIRO
    # (Se o financeiro já foi PAGO, a trava para a operação aqui)
    ledgers_to_cancel = negotiation.ledger_set.all()
    for ledger in ledgers_to_cancel:
        if ledger.status == 'PAID':
            raise ValidationError(f"Impossível cancelar: O lançamento (R$ {ledger.total_value}) desta venda já foi pago/recebido. Estorne o pagamento primeiro.")
            
        ledger.status = 'CANCELED'
        ledger.save()

    # 2. Reverter Itens (Estoque)
    items_to_revert = negotiation.items.all()
    
    # Criamos uma lista separada para os carros da troca, pois vamos deletá-los
    vehicles_from_trade_in = []
    
    for item in items_to_revert:
        if item.flow == 'OUT':
            # O carro que foi VENDIDO (Hilux)
            # Volta a ser da loja e fica disponível
            vehicle = item.vehicle
            vehicle.status = 'AVAILABLE'
            vehicle.current_owner = loja_entity
            vehicle.save()
            
        elif item.flow == 'IN':
            # O carro que entrou na TROCA (Gol)
            # NÃO podemos deletar o 'vehicle' agora por causa da PROTECT.
            # Primeiro, guardamos o carro e o item para deletar depois.
            vehicles_from_trade_in.append((item, item.vehicle))

    # 3. AGORA SIM: Deleta os vínculos e depois os carros da troca
    # Esta é a correção crucial.
    for item_to_delete, vehicle_to_delete in vehicles_from_trade_in:
        # 3.1. Deleta o VÍNCULO (o item do histórico)
        item_to_delete.delete()
        
        # 3.2. Deleta o CARRO (que agora está órfão e desprotegido)
        # Se o carro tiver OS, ele vai travar aqui (o que é bom!)
        vehicle_to_delete.delete()

    # 4. Marcar a Venda como Cancelada
    negotiation.status = 'CANCELED'
    negotiation.save()
    
    return negotiation