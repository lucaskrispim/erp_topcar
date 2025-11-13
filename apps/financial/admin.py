from django.contrib import admin
from .models import FinancialAccount, ChartOfAccounts, Ledger, Installment

@admin.register(FinancialAccount)
class FinancialAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_type', 'balance')

@admin.register(ChartOfAccounts)
class ChartOfAccountsAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'operation_type', 'parent')
    ordering = ('code',)
    # CORREÇÃO CRÍTICA:
    # O Django exige isso para habilitar o autocomplete_fields no LedgerAdmin
    search_fields = ('name', 'code')

class InstallmentInline(admin.TabularInline):
    model = Installment
    extra = 1
    fields = ('installment_number', 'due_date', 'value', 'pay_date', 'paid_value', 'financial_account')

@admin.register(Ledger)
class LedgerAdmin(admin.ModelAdmin):
    list_display = ('description', 'entity', 'total_value', 'transaction_type', 'status', 'due_date', 'vehicle')
    list_filter = ('transaction_type', 'status', 'chart_of_accounts')
    search_fields = ('description', 'entity__nome_razao_social')
    autocomplete_fields = ['entity', 'vehicle', 'chart_of_accounts']
    inlines = [InstallmentInline]