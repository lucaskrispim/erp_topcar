from django.db import models
from core.models import TenantAwareModel
from parties.models import Entity
from employees.models import Employee
from vehicles.models import Vehicle

class Negotiation(TenantAwareModel):
    TYPE_CHOICES = [
        ('SALE', 'Venda'),
        ('PURCHASE', 'Compra'),
        ('CONSIGNMENT', 'Consignação'),
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'Rascunho / Em Aberto'),
        ('APPROVED', 'Aprovada / Fechada'),
        ('CANCELED', 'Cancelada'),
    ]

    # Quem
    customer = models.ForeignKey(Entity, on_delete=models.PROTECT, verbose_name="Cliente/Fornecedor")
    seller = models.ForeignKey(Employee, on_delete=models.PROTECT, verbose_name="Vendedor")
    
    # O Quê
    negotiation_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='SALE')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    negotiation_date = models.DateTimeField(null=True, blank=True, verbose_name="Data do Fechamento")
    
    # Quanto (Saldo Final calculado)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Saldo Final")

    class Meta:
        verbose_name = "Negociação"
        verbose_name_plural = "Negociações"
        ordering = ['-created_at']

    def __str__(self):
        return f"Negociação #{self.id} - {self.customer} ({self.get_status_display()})"


class NegotiationItem(TenantAwareModel):
    FLOW_CHOICES = [
        ('OUT', 'Saída (Venda do Estoque)'),
        ('IN', 'Entrada (Troca/Compra)'),
    ]

    negotiation = models.ForeignKey(Negotiation, on_delete=models.CASCADE, related_name='items')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, verbose_name="Veículo")
    
    agreed_value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Acordado")
    flow = models.CharField(max_length=10, choices=FLOW_CHOICES, verbose_name="Fluxo")

    class Meta:
        verbose_name = "Item da Negociação"
        verbose_name_plural = "Itens da Negociação"
        unique_together = ('negotiation', 'vehicle') # Impede adicionar o mesmo carro 2x na mesma venda

    def __str__(self):
        seta = "->" if self.flow == 'OUT' else "<-"
        return f"{seta} {self.vehicle} (R$ {self.agreed_value})"