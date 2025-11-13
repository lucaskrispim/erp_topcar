from django.db import models
from core.models import TenantAwareModel

class Entity(TenantAwareModel):
    TIPO_ENTIDADE_CHOICES = [
        ('FISICA', 'Pessoa Física'),
        ('JURIDICA', 'Pessoa Jurídica'),
    ]

    nome_razao_social = models.CharField(max_length=255, verbose_name="Nome / Razão Social")
    
    # Unique Index Obrigatório como pedido. 
    # CharField é melhor que Integer para documentos (zeros à esquerda).
    documento_principal = models.CharField(
        max_length=20, 
        unique=True, 
        db_index=True, 
        verbose_name="CPF/CNPJ"
    )
    
    tipo_entidade = models.CharField(
        max_length=10, 
        choices=TIPO_ENTIDADE_CHOICES, 
        default='FISICA'
    )
    
    # Dados de Contato básicos
    email = models.EmailField(null=True, blank=True)
    telefone = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        verbose_name = 'Entidade'
        verbose_name_plural = 'Entidades'
        indexes = [
            models.Index(fields=['nome_razao_social']),
        ]

    def __str__(self):
        return f"{self.nome_razao_social} ({self.documento_principal})"