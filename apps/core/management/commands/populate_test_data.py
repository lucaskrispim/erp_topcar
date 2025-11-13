from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

# Imports dos nossos Apps
from parties.models import Entity
from employees.models import Employee
from vehicles.models import Brand, Model, Vehicle
from financial.models import ChartOfAccounts, FinancialAccount, Ledger
from negotiations.models import Negotiation, NegotiationItem
from negotiations.services import approve_negotiation

User = get_user_model()

class Command(BaseCommand):
    help = 'Popula o banco com dados de teste e executa uma venda completa.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("--- Iniciando Setup de Teste ---")

        # 1. Criar Usuário Admin (se não existir)
        user, created = User.objects.get_or_create(username='admin_teste')
        if created:
            user.set_password('123')
            user.is_superuser = True
            user.is_staff = True
            user.save()
        self.stdout.write(f"1. Usuário: {user.username} (Senha: 123)")

        # 2. Criar Entidades (Atores)
        loja, _ = Entity.objects.get_or_create(
            documento_principal='00000000000191',
            defaults={'nome_razao_social': 'Minha Loja Matriz', 'tipo_entidade': 'JURIDICA'}
        )
        
        cliente, _ = Entity.objects.get_or_create(
            documento_principal='11122233344',
            defaults={'nome_razao_social': 'João Cliente', 'tipo_entidade': 'FISICA'}
        )
        
        vendedor_entity, _ = Entity.objects.get_or_create(
            documento_principal='99988877766',
            defaults={'nome_razao_social': 'Carlos Vendedor', 'tipo_entidade': 'FISICA'}
        )
        self.stdout.write("2. Entidades Criadas.")

        # 3. Criar Colaborador (Vendedor)
        vendedor, _ = Employee.objects.get_or_create(
            entidade=vendedor_entity,
            defaults={'cargo': 'Vendedor Sênior', 'comissao_base_percentual': 1.5, 'usuario_sistema': user}
        )
        self.stdout.write("3. Colaborador Criado.")

        # 4. Criar Veículos (O Estoque e a Troca)
        toyota, _ = Brand.objects.get_or_create(name='Toyota')
        corolla_model, _ = Model.objects.get_or_create(brand=toyota, name='Corolla XEi')
        
        # Carro da Loja (Que será vendido)
        carro_loja, _ = Vehicle.objects.get_or_create(
            chassi='ABC123456789STOCK',
            defaults={
                'model': corolla_model,
                'plate': 'ABC-1234',
                'year_fab': 2022, 'year_model': 2022, 'color': 'Preto',
                'status': 'AVAILABLE', # DISPONÍVEL PARA VENDA
                'acquisition_cost': 80000.00,
                'sale_price': 110000.00,
                'current_owner': loja # A loja é dona
            }
        )

        # Carro do Cliente (Que entrará na troca)
        carro_cliente, _ = Vehicle.objects.get_or_create(
            chassi='XYZ987654321TRADE',
            defaults={
                'model': corolla_model, # Usando o mesmo modelo pra simplificar
                'plate': 'XYZ-9876',
                'year_fab': 2015, 'year_model': 2015, 'color': 'Prata',
                'status': 'AVAILABLE', 
                'acquisition_cost': 0, # Irrelevante agora
                'sale_price': 0,
                'current_owner': cliente # O cliente é dono
            }
        )
        self.stdout.write("4. Veículos Criados (1 Estoque, 1 Cliente).")

        # 5. Configurar Financeiro
        receita, _ = ChartOfAccounts.objects.get_or_create(
            code='1.01', defaults={'name': 'Receita Venda Veículos', 'operation_type': 'REVENUE'}
        )
        # O código exige o 2.01 para troco/custo, vamos criar para garantir
        despesa, _ = ChartOfAccounts.objects.get_or_create(
            code='2.01', defaults={'name': 'Custo Aquisição Veículos', 'operation_type': 'EXPENSE'}
        )
        self.stdout.write("5. Plano de Contas Configurado.")

        # 6. Criar a Negociação (Rascunho)
        negociacao = Negotiation.objects.create(
            customer=cliente,
            seller=vendedor,
            negotiation_type='SALE',
            status='DRAFT',
            total_value=0
        )

        # 6.1 Item 1: Venda do Corolla Preto (Saída) - Valor: 100k (Desconto de 10k sobre tabela)
        NegotiationItem.objects.create(
            negotiation=negociacao,
            vehicle=carro_loja,
            flow='OUT',
            agreed_value=100000.00
        )

        # 6.2 Item 2: Entrada do Corolla Prata (Entrada) - Valor: 60k
        NegotiationItem.objects.create(
            negotiation=negociacao,
            vehicle=carro_cliente,
            flow='IN',
            agreed_value=60000.00
        )
        # SALDO ESPERADO: 100k - 60k = 40k a receber
        self.stdout.write("6. Negociação Rascunhada (Venda 100k - Troca 60k).")

        # 7. APROVAR (O Teste de Fogo)
        self.stdout.write(">>> Executando Serviço de Aprovação...")
        try:
            negociacao_aprovada = approve_negotiation(negociacao.id, user)
            self.stdout.write(self.style.SUCCESS(f"SUCESSO! Negociação #{negociacao_aprovada.id} Aprovada."))
            self.stdout.write(f"Saldo Final: R$ {negociacao_aprovada.total_value}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"ERRO NA APROVAÇÃO: {e}"))
            raise e # Re-raise para rollback

        # 8. Verificações Finais
        carro_loja.refresh_from_db()
        carro_cliente.refresh_from_db()
        ledger_count = Ledger.objects.filter(negotiation=negociacao).count()

        self.stdout.write("--- RESULTADOS ---")
        self.stdout.write(f"Status Carro Vendido (ABC-1234): {carro_loja.status} (Esperado: SOLD)")
        self.stdout.write(f"Status Carro Entrado (XYZ-9876): {carro_cliente.status} (Esperado: MAINTENANCE)")
        self.stdout.write(f"Dono Carro Entrado: {carro_cliente.current_owner.nome_razao_social}") # Deveria ser loja se tivéssemos ajustado a lógica de dono
        self.stdout.write(f"Lançamentos Financeiros Gerados: {ledger_count}")

        # 9. Teste de Manutenção (O Custo Real)
        self.stdout.write("--- Testando Manutenção (Service Order) ---")
        
        # 9.1 Criar Categoria de Manutenção
        manutencao_cat, _ = ChartOfAccounts.objects.get_or_create(
            code='3.01', defaults={'name': 'Manutenção de Estoque', 'operation_type': 'EXPENSE'}
        )
        
        # 9.2 Criar Fornecedor (Mecânico)
        mecanico, _ = Entity.objects.get_or_create(
            documento_principal='55566677788',
            defaults={'nome_razao_social': 'Oficina do Zé', 'tipo_entidade': 'PJ'}
        )

        # 9.3 Criar OS para o Carro da Troca (XYZ-9876) que entrou em manutenção
        from maintenance.models import ServiceOrder, ServiceOrderItem
        from maintenance.services import complete_service_order
        
        os = ServiceOrder.objects.create(
            vehicle=carro_cliente, # O carro prata da troca
            supplier=mecanico,
            status='APPROVED',
            total_cost=0
        )
        
        ServiceOrderItem.objects.create(service_order=os, description="Troca de Óleo", cost=300.00, category='MECHANIC')
        ServiceOrderItem.objects.create(service_order=os, description="Polimento", cost=200.00, category='AESTHETICS')
        
        self.stdout.write(f"OS #{os.id} Criada para {carro_cliente}. Valor previsto: 500.00")

        # 9.4 Concluir OS
        complete_service_order(os.id, user)
        self.stdout.write(self.style.SUCCESS(f"OS #{os.id} Concluída! Financeiro Gerado."))

        # 9.5 Validar Custo Real
        # Lucro do Carro Prata (futuro) = Preço Venda - (Valor Pago na Troca + Custo Manutenção)
        # Custo Total Atual no sistema = 60.000 (Troca) + 500 (OS) = 60.500
        total_custo_ledger = Ledger.objects.filter(vehicle=carro_cliente, transaction_type='PAYABLE').count() # Deve ser 2 (1 da troca, 1 da OS)
        self.stdout.write(f"Lançamentos de Custo para o Carro Prata: {total_custo_ledger} (Esperado: 2 - Troca e Oficina)")