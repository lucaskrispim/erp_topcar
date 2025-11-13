from django.db import models

from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    """
    Apenas para AUTENTICAÇÃO.
    Não adicione 'cpf', 'endereco' ou 'cargo' aqui.
    """
    # Adicione campos apenas se forem estritamente de sistema/login
    # Ex: avatar (ok), bio (ok), mas nada de regra de negócio.
    
    class Meta:
        verbose_name = 'Usuário do Sistema'
        verbose_name_plural = 'Usuários do Sistema'

    def __str__(self):
        return self.username


class TenantAwareModel(models.Model):
    """
    Classe abstrata que injeta auditoria e multi-tenancy (Loja)
    em todas as tabelas que herdarem dela.
    """
    # TODO: Futuramente isso será FK para uma tabela de Lojas.
    # Por enquanto, usamos um ID fixo ou Integer para facilitar o start.
    loja_id = models.IntegerField(default=1, verbose_name="ID da Loja")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    # Rastreabilidade: Quem criou este registro?
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created_by",
        verbose_name="Criado por"
    )

    class Meta:
        abstract = True
