from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Vehicle
from parties.models import Entity
from financial.models import Ledger, ChartOfAccounts

def register_vehicle_acquisition(vehicle_data, seller_data, user, loja_id=1):
    """
    Orquestra a entrada de um veículo comprado:
    1. Cadastra/Busca o Vendedor (Entity).
    2. Cadastra o Veículo (Vehicle).
    3. Gera o Contas a Pagar (Ledger).
    """
    with transaction.atomic():
        # 1. Resolver o Vendedor (Quem nos vendeu?)
        # Tenta buscar pelo CPF/CNPJ, se não existir, cria.
        seller, created = Entity.objects.get_or_create(
            documento_principal=seller_data['document'],
            defaults={
                'nome_razao_social': seller_data['name'],
                'tipo_entidade': 'FISICA' if len(seller_data['document']) <= 11 else 'JURIDICA',
                'loja_id': loja_id,
                'created_by': user
            }
        )

        # 2. Resolver o Dono Atual (A Loja)
        # Assumimos que a loja é a Entity ID 1 (criada no seed). 
        # Em produção, isso viria de config('LOJA_DEFAULT_ID')
        try:
            loja_entity = Entity.objects.get(id=loja_id) # Ou filtrar por CNPJ da loja
        except Entity.DoesNotExist:
            # Fallback de segurança para ambiente de dev
            loja_entity = seller 

        # 3. Criar o Veículo
        vehicle = Vehicle.objects.create(
            model=vehicle_data['model'],
            chassi=vehicle_data['chassi'],
            plate=vehicle_data['plate'],
            renavam=vehicle_data['renavam'],
            year_fab=vehicle_data['year_fab'],
            year_model=vehicle_data['year_model'],
            color=vehicle_data['color'],
            fuel_type=vehicle_data['fuel_type'],
            mileage=vehicle_data['mileage'],
            status='AVAILABLE', # Entra disponível para venda
            acquisition_cost=vehicle_data['acquisition_cost'], # R$ 40.000
            sale_price=vehicle_data['sale_price'],             # R$ 55.000 (Sugestão)
            current_owner=loja_entity, # O dono agora é a loja!
            notes=vehicle_data.get('notes', ''),
            loja_id=loja_id,
            created_by=user
        )

        # 4. Gerar Financeiro (Obrigação de Pagar a Compra)
        # Só gera se houver custo de aquisição > 0
        if vehicle.acquisition_cost > 0:
            try:
                categoria_aquisicao = ChartOfAccounts.objects.get(code='2.01') # Custo Aquisição
            except ChartOfAccounts.DoesNotExist:
                raise ValidationError("Erro Crítico: Categoria contábil '2.01' não encontrada.")

            Ledger.objects.create(
                entity=seller, # Devemos ao Vendedor
                chart_of_accounts=categoria_aquisicao,
                vehicle=vehicle, # Centro de custo
                total_value=vehicle.acquisition_cost,
                transaction_type='PAYABLE',
                status='OPEN', # Em aberto para pagar depois
                due_date=timezone.now().date(), # Vence hoje (pode parametrizar)
                description=f"Aquisição Veículo {vehicle.model} Placa {vehicle.plate}",
                loja_id=loja_id,
                created_by=user
            )

    return vehicle