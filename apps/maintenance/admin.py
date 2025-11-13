from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import ServiceOrder, ServiceOrderItem
from .services import complete_service_order # Vamos criar isso já já

class ServiceOrderItemInline(admin.TabularInline):
    model = ServiceOrderItem
    extra = 1

@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'vehicle', 'supplier', 'status', 'total_cost', 'issue_date')
    list_filter = ('status', 'issue_date')
    search_fields = ('vehicle__plate', 'vehicle__chassi', 'supplier__nome_razao_social')
    autocomplete_fields = ['vehicle', 'supplier']
    inlines = [ServiceOrderItemInline]
    actions = ['complete_os_action']

    @admin.action(description='Concluir OS e Gerar Financeiro')
    def complete_os_action(self, request, queryset):
        for os in queryset:
            try:
                complete_service_order(os.id, request.user)
                self.message_user(request, f"OS #{os.id} concluída e contas a pagar gerada!", messages.SUCCESS)
            except ValidationError as e:
                self.message_user(request, f"Erro na OS #{os.id}: {e.message}", messages.ERROR)
            except Exception as e:
                self.message_user(request, f"Erro sistêmico na OS #{os.id}: {str(e)}", messages.ERROR)