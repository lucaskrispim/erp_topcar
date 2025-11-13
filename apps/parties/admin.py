from django.contrib import admin
from .models import Entity

@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ('nome_razao_social', 'documento_principal', 'tipo_entidade')
    search_fields = ('nome_razao_social', 'documento_principal') # Obrigatório para autocomplete