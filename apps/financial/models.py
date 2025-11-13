from django.db import models
from django.core.exceptions import ValidationError
from core.models import TenantAwareModel
from parties.models import Entity
from vehicles.models import Vehicle

class FinancialAccount(TenantAwareModel):
    TYPE_CHOICES = [
        ('CASH', 'Caixa Físico'),
        ('BANK', 'Conta Bancária'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Nome da Conta")
    account_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='BANK')
    
    # Este saldo deve ser recalculado a cada movimentação para garantir integridade
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="Saldo Atual")

    class Meta:
        verbose_name = "Conta Financeira"
        verbose_name_plural = "Contas Financeiras"

    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()})"


class ChartOfAccounts(TenantAwareModel):
    OPERATION_CHOICES = [
        ('REVENUE', 'Receita'),
        ('EXPENSE', 'Despesa'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Nome da Categoria")
    code = models.CharField(max_length=20, unique=True, verbose_name="Código Contábil") # Ex: 1.01
    operation_type = models.CharField(max_length=10, choices=OPERATION_CHOICES)
    
    # Auto-relacionamento para hierarquia (Ex: Despesas -> Fixas -> Aluguel)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class Meta:
        verbose_name = "Plano de Contas"
        verbose_name_plural = "Planos de Contas"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Ledger(TenantAwareModel):
    TRANS_TYPE_CHOICES = [
        ('PAYABLE', 'A Pagar'),
        ('RECEIVABLE', 'A Receber'),
    ]
    
    STATUS_CHOICES = [
        ('OPEN', 'Em Aberto'),
        ('PARTIAL', 'Pago Parcialmente'),
        ('PAID', 'Quitado'),
        ('CANCELED', 'Cancelado'),
    ]

    # --- Quem e O Quê ---
    entity = models.ForeignKey(Entity, on_delete=models.PROTECT, verbose_name="Entidade (Parceiro)")
    chart_of_accounts = models.ForeignKey(ChartOfAccounts, on_delete=models.PROTECT, verbose_name="Categoria")
    
    # O Centro de Custo Real. Se preenchido, afeta o lucro do carro.
    vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='lancamentos',
        verbose_name="Veículo (Centro de Custo)"
    )

    # --- Valores e Datas ---
    total_value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Total")
    transaction_type = models.CharField(max_length=15, choices=TRANS_TYPE_CHOICES, verbose_name="Tipo")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='OPEN', db_index=True)
    due_date = models.DateField(db_index=True, verbose_name="Data de Competência/Vencimento")
    description = models.TextField(verbose_name="Histórico/Descrição")

    # --- Link com Vendas (Futuro) ---
    # TODO: Descomentar no Passo 4 quando criarmos o app 'negotiations'
    negotiation = models.ForeignKey(
        'negotiations.Negotiation', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Origem da Negociação"
    )

    class Meta:
        verbose_name = "Lançamento (Ledger)"
        verbose_name_plural = "Lançamentos"
        indexes = [
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['transaction_type']),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.description} ({self.total_value})"


class Installment(TenantAwareModel):
    PAYMENT_METHODS = [
        ('CASH', 'Dinheiro'),
        ('TRANSFER', 'TED/PIX'),
        ('BOLETO', 'Boleto'),
        ('CREDIT_CARD', 'Cartão Crédito'),
        ('FINANCING', 'Financiamento'),
    ]

    ledger = models.ForeignKey(Ledger, on_delete=models.CASCADE, related_name='parcelas')
    
    # Nullable pois na previsão (Aberto) ainda não sabemos de onde sairá o dinheiro.
    financial_account = models.ForeignKey(
        FinancialAccount, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        verbose_name="Conta Movimentada"
    )
    
    installment_number = models.PositiveIntegerField(verbose_name="Nº Parcela")
    due_date = models.DateField(verbose_name="Vencimento")
    
    # Se preenchido, considera-se pago.
    pay_date = models.DateField(null=True, blank=True, verbose_name="Data Pagamento")
    
    value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Parcela")
    paid_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Valor Pago")
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, null=True, blank=True, verbose_name="Forma Pagto")

    class Meta:
        verbose_name = "Parcela / Movimentação"
        verbose_name_plural = "Parcelas"
        unique_together = ('ledger', 'installment_number')

    def __str__(self):
        return f"Parc {self.installment_number} - {self.ledger}"

    def clean(self):
        # Validação crítica: Se tem data de pagamento, TEM que ter Conta Financeira e Método
        if self.pay_date and not self.financial_account:
             raise ValidationError("Para confirmar o pagamento, informe a Conta Financeira.")
        
        if self.pay_date and not self.payment_method:
             raise ValidationError("Para confirmar o pagamento, informe a Forma de Pagamento.")