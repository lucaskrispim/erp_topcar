from django.db import models
from django.conf import settings
from core.models import TenantAwareModel
from parties.models import Entity

class Employee(TenantAwareModel):
    # Vínculo 1: Quem é a pessoa física?
    entidade = models.OneToOneField(
        Entity,
        on_delete=models.PROTECT, # Se apagar a entidade, bloqueia.
        related_name='colaborador_profile',
        verbose_name="Dados Pessoais (Entidade)"
    )
    
    # Vínculo 2: Qual é o login dele?
    # Nullable: Um funcionário pode ser cadastrado antes de ter um login de sistema.
    usuario_sistema = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='funcionario_profile',
        verbose_name="Usuário de Acesso"
    )
    
    cargo = models.CharField(max_length=100)
    
    # Decimal para financeiro sempre. Float é para cientistas.
    comissao_base_percentual = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Comissão Base (%)"
    )
    
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Colaborador'
        verbose_name_plural = 'Colaboradores'

    def __str__(self):
        return f"{self.entidade.nome_razao_social} - {self.cargo}"