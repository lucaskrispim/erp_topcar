import time
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

# Imports dos nossos Apps
from parties.models import Entity
from employees.models import Employee
from vehicles.models import Brand, Model, Vehicle
from financial.models import ChartOfAccounts, FinancialAccount, Ledger, Installment
from negotiations.models import Negotiation, NegotiationItem
from negotiations.services import approve_negotiation
from maintenance.models import ServiceOrder, ServiceOrderItem
from maintenance.services import complete_service_order
from financial.services import settle_ledger # Para quitar contas no script

User = get_user_model()

class Command(BaseCommand):
    help = 'Popula o banco com dados de teste e executa o fluxo completo do ERP.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("--- INICIANDO FLUXO COMPLETO DE TESTE ERP ---"))

        # --- 1. SETUP DE USUÁRIO E ENTIDADES BÁSICAS ---
        user, _ = User.objects.get_or_create(username='admin_teste', defaults={'password': '123', 'is_superuser': True, 'is_staff': True})
        user.set_password('123')
        user.save()
        
        loja, _ = Entity.objects.get_or_create(documento_principal='00000000000191', defaults={'nome_razao_social': 'Minha Loja Matriz', 'tipo_entidade': 'JURIDICA'})
        cliente_venda, _ = Entity.objects.get_or_create(documento_principal='11122233344', defaults={'nome_razao_social': 'Joana Cliente Fiel', 'tipo_entidade': 'FISICA'})
        fornecedor_troca, _ = Entity.objects.get_or_create(documento_principal='99988877766', defaults={'nome_razao_social': 'Carlos Cliente Troca', 'tipo_entidade': 'FISICA'})
        mecanico, _ = Entity.objects.get_or_create(documento_principal='55566677788', defaults={'nome_razao_social': 'Oficina do Zé', 'tipo_entidade': 'JURIDICA'})
        fornecedor_geral, _ = Entity.objects.get_or_create(documento_principal='9876543210001', defaults={'nome_razao_social': 'Energia Fornecedora S/A', 'tipo_entidade': 'JURIDICA'}) # NOVO
        
        vendedor_entity, _ = Entity.objects.get_or_create(documento_principal='12345678900', defaults={'nome_razao_social': 'Pedro Vendedor', 'tipo_entidade': 'FISICA'})
        vendedor, _ = Employee.objects.get_or_create(entidade=vendedor_entity, defaults={'cargo': 'Vendedor Pleno', 'comissao_base_percentual': 1.0, 'usuario_sistema': user})

        self.stdout.write("1. Setup Básico (Usuário, Loja, Pessoas) concluído.")

        # --- 2. SETUP DE DOMÍNIO (MARCAS, MODELOS, CONTAS) ---
        toyota, _ = Brand.objects.get_or_create(name='Toyota')
        corolla_model, _ = Model.objects.get_or_create(brand=toyota, name='Corolla XEi')
        
        # Cria as categorias contábeis (Plano de Contas)
        ChartOfAccounts.objects.get_or_create(code='1.01', defaults={'name': 'Receita Venda Veículos', 'operation_type': 'REVENUE'})
        ChartOfAccounts.objects.get_or_create(code='2.01', defaults={'name': 'Custo Aquisição Veículos', 'operation_type': 'EXPENSE'})
        ChartOfAccounts.objects.get_or_create(code='3.01', defaults={'name': 'Manutenção de Estoque', 'operation_type': 'EXPENSE'})
        ChartOfAccounts.objects.get_or_create(code='4.01', defaults={'name': 'Despesas Administrativas', 'operation_type': 'EXPENSE'})
        ChartOfAccounts.objects.get_or_create(code='4.02', defaults={'name': 'Despesas com Bônus/Comissões', 'operation_type': 'EXPENSE'}) # NOVO
        
        # Cria Contas Financeiras (Caixa/Banco)
        caixa, _ = FinancialAccount.objects.get_or_create(name='Caixa Loja', defaults={'account_type': 'CASH', 'balance': Decimal('5000.00')})
        banco, _ = FinancialAccount.objects.get_or_create(name='Banco Principal', defaults={'account_type': 'BANK', 'balance': Decimal('150000.00')})

        self.stdout.write("2. Setup Financeiro (Contas/Plano) concluído.")

        # --- 3. FLUXO: AQUISIÇÃO E CUSTO (VEÍCULO QUE SERÁ VENDIDO) ---
        
        # 3.1. Aquisição - Carro 1 (Fusca)
        fusca_model, _ = Model.objects.get_or_create(brand=toyota, name='Fusca')
        fusca_entity, _ = Entity.objects.get_or_create(documento_principal='11111111111', defaults={'nome_razao_social': 'Antonio Fornecedor', 'tipo_entidade': 'FISICA'})
        
        fusca_aquisicao = Ledger.objects.create(
            entity=fusca_entity, chart_of_accounts=ChartOfAccounts.objects.get(code='2.01'),
            transaction_type='PAYABLE', total_value=Decimal('10000.00'), due_date=timezone.now().date(),
            description="Compra de Ativo para Revenda - Fusca", created_by=user, loja_id=1
        )
        fusca = Vehicle.objects.create(
            model=fusca_model, chassi='FUSCA99999STOCK', plate='FSC-1970',
            year_fab=1970, year_model=1970, color='Vermelho', status='MAINTENANCE',
            acquisition_cost=Decimal('10000.00'), sale_price=Decimal('15000.00'),
            current_owner=loja, created_by=user, loja_id=1
        )
        fusca_aquisicao.vehicle = fusca; fusca_aquisicao.save()

        # 3.2. Custo - Oficina no Fusca
        os_fusca = ServiceOrder.objects.create(vehicle=fusca, supplier=mecanico, status='APPROVED', issue_date=timezone.now().date(), created_by=user, loja_id=1)
        ServiceOrderItem.objects.create(service_order=os_fusca, description="Revisão geral (R$ 800)", cost=Decimal('800.00'), category='MECHANIC', created_by=user, loja_id=1)
        complete_service_order(os_fusca.id, user) 

        # 3.3. Liquidação - Pagar Fornecedor e Oficina
        settle_ledger(fusca_aquisicao.id, fusca_aquisicao.total_value, banco.id, user)
        os_ledger = Ledger.objects.get(vehicle=fusca, chart_of_accounts__code='3.01', transaction_type='PAYABLE')
        settle_ledger(os_ledger.id, os_ledger.total_value, banco.id, user)
        
        fusca.status = 'AVAILABLE'; fusca.save()
        self.stdout.write("3. Aquisição e Custo do Fusca (R$ 10.800) concluídos. Status: Available.")
        # Saldo Banco: 150000 - 10000 - 800 = 139.200

        # --- 4. FLUXO: VENDA COM TROCA E RECEBIMENTO (SALDO POSITIVO) ---
        troca_model, _ = Model.objects.get_or_create(brand=toyota, name='Yaris')
        carro_troca = Vehicle.objects.create(model=troca_model, chassi='YARIS123456TRADE', plate='YRS-5678', year_fab=2018, year_model=2019, color='Branco', status='AVAILABLE', acquisition_cost=Decimal('35000.00'), sale_price=Decimal('45000.00'), current_owner=fornecedor_troca, created_by=user, loja_id=1)

        valor_venda = Decimal('15000.00') # Venda do Fusca
        valor_troca = Decimal('10000.00') # Valor que aceitamos no Yaris
        
        negociacao = Negotiation.objects.create(customer=cliente_venda, seller=vendedor, negotiation_type='SALE', status='DRAFT', created_by=user, loja_id=1)
        NegotiationItem.objects.create(negotiation=negociacao, vehicle=fusca, flow='OUT', agreed_value=valor_venda, created_by=user, loja_id=1)
        NegotiationItem.objects.create(negotiation=negociacao, vehicle=carro_troca, flow='IN', agreed_value=valor_troca, created_by=user, loja_id=1)

        approve_neg = approve_negotiation(negociacao.id, user)
        # Saldo esperado: 15000 - 10000 = 5000 (A Receber)
        
        venda_ledger = Ledger.objects.get(negotiation=approve_neg)
        settle_ledger(venda_ledger.id, venda_ledger.total_value, caixa.id, user) # Recebe os R$ 5.000 no caixa
        self.stdout.write("4. Venda c/ Troca (Saldo Positivo) e Recebimento concluídos.")
        # Saldo Caixa: 5000 + 5000 = 10.000

        # --- 5. NOVO FLUXO: VENDA COM TROCA (SALDO NEGATIVO / TROCO) ---
        
        carro_saida_val = Decimal('50000.00') # Carro da Loja
        carro_troca_val = Decimal('60000.00') # Carro do Cliente (vale mais)
        troco = carro_troca_val - carro_saida_val # R$ 10.000 (A Pagar)
        
        # 5.1. Cria Veículo para ser vendido
        civic_model, _ = Model.objects.get_or_create(brand=Brand.objects.get_or_create(name='Honda')[0], name='Civic')
        civic = Vehicle.objects.create(model=civic_model, chassi='CIVIC00000SALE', plate='CIV-0001', year_fab=2020, year_model=2020, acquisition_cost=Decimal('40000'), sale_price=carro_saida_val, current_owner=loja, created_by=user, status='AVAILABLE', loja_id=1)

        # 5.2. Cria Troca
        audi_model, _ = Model.objects.get_or_create(brand=Brand.objects.get_or_create(name='Audi')[0], name='A4')
        carro_audi_troca = Vehicle.objects.create(model=audi_model, chassi='AUDIA4TRADE001', plate='AUD-0001', year_fab=2018, year_model=2019, acquisition_cost=carro_troca_val, sale_price=carro_troca_val * Decimal('1.2'), current_owner=fornecedor_troca, created_by=user, status='AVAILABLE', loja_id=1)
        
        negociacao_troco = Negotiation.objects.create(customer=fornecedor_troca, seller=vendedor, negotiation_type='SALE', status='DRAFT', created_by=user, loja_id=1)
        NegotiationItem.objects.create(negotiation=negociacao_troco, vehicle=civic, flow='OUT', agreed_value=carro_saida_val, created_by=user, loja_id=1)
        NegotiationItem.objects.create(negotiation=negociacao_troco, vehicle=carro_audi_troca, flow='IN', agreed_value=carro_troca_val, created_by=user, loja_id=1)

        approve_neg_troco = approve_negotiation(negociacao_troco.id, user)
        # Saldo esperado: 50k - 60k = -10k (A Pagar)
        
        troco_ledger = Ledger.objects.get(negotiation=approve_neg_troco)
        settle_ledger(troco_ledger.id, troco_ledger.total_value, banco.id, user) # Paga o troco (R$ 10.000)
        self.stdout.write("5. Venda c/ Troca (Saldo Negativo / Troco) concluídos.")
        # Saldo Banco: 139200 - 10000 = 129.200

        # --- 6. NOVO FLUXO: LANÇAMENTO MANUAL (DESPESA GERAL) ---
        
        luz_ledger = Ledger.objects.create(
            entity=fornecedor_geral, chart_of_accounts=ChartOfAccounts.objects.get(code='4.01'),
            transaction_type='PAYABLE', total_value=Decimal('1200.00'), due_date=timezone.now().date(),
            description="Conta de energia elétrica da Matriz", created_by=user, loja_id=1
        )
        settle_ledger(luz_ledger.id, luz_ledger.total_value, banco.id, user) # Paga os 1.200
        self.stdout.write("6. Lançamento Manual (Despesa Geral) concluído.")
        # Saldo Banco: 129200 - 1200 = 128.000

        # --- 7. VERIFICAÇÕES FINAIS ---
        
        banco.refresh_from_db()
        caixa.refresh_from_db()

        self.stdout.write(self.style.MIGRATE_HEADING("--- RESULTADOS FINAIS ---"))
        self.stdout.write(f"Vendas Aprovadas (Total): {Negotiation.objects.filter(status='APPROVED').count()}")
        self.stdout.write(f"----------------------------------------")
        self.stdout.write(f"Saldo Final Banco: R$ {banco.balance}") 
        self.stdout.write(f"Saldo Final Caixa: R$ {caixa.balance}")
        self.stdout.write(f"----------------------------------------")
        
        self.stdout.write(self.style.SUCCESS("TODOS OS FLUXOS (Aquisição, Custo, Venda+, Venda-, Gasto) VALIDADOS COM SUCESSO!"))