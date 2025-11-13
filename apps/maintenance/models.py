from django.db import models
from core.models import TenantAwareModel
from vehicles.models import Vehicle
from parties.models import Entity

class ServiceOrder(TenantAwareModel):
    STATUS_CHOICES = [
        ('REQUESTED', 'Solicitada'),
        ('APPROVED', 'Aprovada / Em Execução'),
        ('COMPLETED', 'Concluída'),
        ('CANCELED', 'Cancelada'),
    ]

    # O Centro de Custo (Obrigatório)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='service_orders', verbose_name="Veículo")
    
    # O Fornecedor (Mecânico, Funileiro, Posto de Lavagem)
    supplier = models.ForeignKey(Entity, on_delete=models.PROTECT, related_name='services_provided', verbose_name="Fornecedor")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    
    # Data de Emissão e Previsão
    issue_date = models.DateField(auto_now_add=True, verbose_name="Data de Emissão")
    completion_date = models.DateField(null=True, blank=True, verbose_name="Data de Conclusão")
    
    # Custo Total (Cache calculado via serviço)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Custo Total")
    
    notes = models.TextField(null=True, blank=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Ordem de Serviço (OS)"
        verbose_name_plural = "Ordens de Serviço"

    def __str__(self):
        return f"OS #{self.id} - {self.vehicle} ({self.get_status_display()})"


class ServiceOrderItem(TenantAwareModel):
    CATEGORY_CHOICES = [
        ('MECHANIC', 'Mecânica'),
        ('BODYWORK', 'Funilaria/Pintura'),
        ('AESTHETICS', 'Estética/Lavagem'),
        ('PARTS', 'Peças'),
        ('DOCUMENTATION', 'Documentação/Despachante'),
        ('OTHER', 'Outros'),
    ]

    service_order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255, verbose_name="Descrição do Serviço/Peça")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='MECHANIC', verbose_name="Categoria")
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Custo")

    class Meta:
        verbose_name = "Item da OS"
        verbose_name_plural = "Itens da OS"

    def __str__(self):
        return f"{self.description} (R$ {self.cost})"