from django.db import models
from django.core.exceptions import ValidationError
from core.models import TenantAwareModel
from parties.models import Entity

class Brand(TenantAwareModel):
    name = models.CharField(max_length=100, unique=True, verbose_name="Marca")

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ['name']

    def __str__(self):
        return self.name


class Model(TenantAwareModel):
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='models', verbose_name="Marca")
    name = models.CharField(max_length=100, verbose_name="Nome do Modelo")

    class Meta:
        verbose_name = "Modelo"
        verbose_name_plural = "Modelos"
        ordering = ['brand__name', 'name']

    def __str__(self):
        return f"{self.brand.name} {self.name}"


class Vehicle(TenantAwareModel):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Disponível'),
        ('MAINTENANCE', 'Em Manutenção'),
        ('RESERVED', 'Reservado'),
        ('SOLD', 'Vendido'),
        ('WRITE_OFF', 'Baixado / Perda Total'),
    ]

    FUEL_CHOICES = [
        ('GASOLINE', 'Gasolina'),
        ('ETHANOL', 'Etanol'),
        ('FLEX', 'Flex'),
        ('DIESEL', 'Diesel'),
        ('HYBRID', 'Híbrido'),
        ('ELECTRIC', 'Elétrico'),
    ]

    # --- Identificação ---
    model = models.ForeignKey(Model, on_delete=models.PROTECT, verbose_name="Modelo")
    
    # Chassi: Indexado pois é a busca mais precisa. Unique.
    chassi = models.CharField(max_length=50, unique=True, db_index=True, verbose_name="Chassi")
    
    # Placa: Pode ser nula (carro 0km), mas se tiver, é única.
    plate = models.CharField(max_length=10, unique=True, null=True, blank=True, db_index=True, verbose_name="Placa")
    renavam = models.CharField(max_length=20, null=True, blank=True, verbose_name="Renavam")

    # --- Características ---
    year_fab = models.PositiveIntegerField(verbose_name="Ano Fab.")
    year_model = models.PositiveIntegerField(verbose_name="Ano Mod.")
    color = models.CharField(max_length=30, verbose_name="Cor")
    mileage = models.PositiveIntegerField(default=0, verbose_name="Quilometragem (KM)")
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES, default='FLEX', verbose_name="Combustível")

    # --- Negócio & Financeiro ---
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE', db_index=True)
    
    # Decimais: Sempre use DecimalField para dinheiro. Float gera erros de arredondamento.
    acquisition_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Custo de Aquisição")
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de Venda")

    # --- Propriedade ---
    # Quem é o dono legal do carro no momento? 
    # Se for da Loja, aponta para a Entidade "Minha Loja". Se for consignado, aponta para o Cliente.
    current_owner = models.ForeignKey(
        Entity, 
        on_delete=models.PROTECT, 
        related_name='veiculos_proprietario',
        verbose_name="Proprietário Atual"
    )
    
    notes = models.TextField(null=True, blank=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Veículo"
        verbose_name_plural = "Veículos"
        indexes = [
            models.Index(fields=['status', 'model']), # Índice composto para filtros comuns
        ]

    def __str__(self):
        # Ex: Toyota Corolla (ABC-1234)
        placa_display = self.plate if self.plate else "SEM PLACA"
        return f"{self.model} ({placa_display}) - {self.get_status_display()}"

    def clean(self):
        # Normalização de dados antes de salvar
        if self.chassi:
            self.chassi = self.chassi.upper().strip()
        if self.plate:
            self.plate = self.plate.upper().strip()