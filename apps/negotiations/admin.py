from django.contrib import admin
from .models import Negotiation, NegotiationItem

from django.contrib import messages
from django.core.exceptions import ValidationError
from .services import approve_negotiation # Importe a função criada

class NegotiationItemInline(admin.TabularInline):
    model = NegotiationItem
    extra = 1
    autocomplete_fields = ['vehicle'] # Vital para não carregar 10mil carros no dropdown

@admin.register(Negotiation)
class NegotiationAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'seller', 'negotiation_type', 'status', 'total_value', 'created_at')
    list_filter = ('status', 'negotiation_type', 'created_at')
    search_fields = ('customer__nome_razao_social', 'seller__entidade__nome_razao_social')
    autocomplete_fields = ['customer', 'seller']
    inlines = [NegotiationItemInline]

    actions = ['approve_negotiations_action']
    
    # Read-only se estiver aprovada para garantir integridade
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status in ['APPROVED', 'CANCELED']:
            return [f.name for f in self.model._meta.fields]
        return []
    

    @admin.action(description='Aprovar Negociações Selecionadas')
    def approve_negotiations_action(self, request, queryset):
        for negotiation in queryset:
            try:
                approve_negotiation(negotiation.id, request.user)
                self.message_user(request, f"Negociação #{negotiation.id} aprovada com sucesso!", messages.SUCCESS)
            except ValidationError as e:
                self.message_user(request, f"Erro na #{negotiation.id}: {e.message}", messages.ERROR)
            except Exception as e:
                self.message_user(request, f"Erro sistêmico na #{negotiation.id}: {str(e)}", messages.ERROR)