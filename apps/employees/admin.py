from django.contrib import admin
from .models import Employee

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('entidade', 'cargo', 'ativo', 'comissao_base_percentual')
    list_filter = ('ativo', 'cargo')
    
    # CRÍTICO: O Django exige search_fields aqui para que o 
    # autocomplete_fields do NegotiationAdmin funcione.
    search_fields = ('entidade__nome_razao_social', 'entidade__documento_principal', 'cargo')
    
    # Para facilitar a criação, usamos autocomplete na entidade (Pessoa) também
    autocomplete_fields = ['entidade']