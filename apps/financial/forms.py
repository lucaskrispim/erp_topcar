from django import forms
from .models import Ledger, ChartOfAccounts, FinancialAccount
from vehicles.models import Vehicle
from parties.models import Entity

class ManualLedgerForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra o plano de contas para não mostrar "Receita" quando for "A Pagar", etc.
        # (Por enquanto, mostramos todos)
        self.fields['chart_of_accounts'].queryset = ChartOfAccounts.objects.all().order_by('code')
        self.fields['entity'].queryset = Entity.objects.all().order_by('nome_razao_social')
        
        # Veículo é opcional (para despesas gerais), mas filtramos os vendidos
        self.fields['vehicle'].queryset = Vehicle.objects.exclude(status='SOLD').order_by('model')

    class Meta:
        model = Ledger
        fields = [
            'transaction_type', 'entity', 'chart_of_accounts', 
            'vehicle', 'total_value', 'due_date', 'description'
        ]
        labels = {
            'transaction_type': 'Tipo de Transação',
            'entity': 'Para/De quem (Cliente/Fornecedor)',
            'chart_of_accounts': 'Categoria (Plano de Contas)',
            'vehicle': 'Veículo (Opcional - Centro de Custo)',
            'total_value': 'Valor Total (R$)',
            'due_date': 'Data de Vencimento',
            'description': 'Histórico / Descrição'
        }
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'entity': forms.Select(attrs={'class': 'form-select'}),
            'chart_of_accounts': forms.Select(attrs={'class': 'form-select'}),
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'total_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ... (imports anteriores: Ledger, ChartOfAccounts, etc.) ...

# --- FORMULÁRIO DE PLANO DE CONTAS (CRUD) ---
class ChartOfAccountsForm(forms.ModelForm):
    class Meta:
        model = ChartOfAccounts
        fields = ['name', 'code', 'operation_type', 'parent']
        labels = {
            'name': 'Nome da Categoria',
            'code': 'Código Contábil',
            'operation_type': 'Tipo de Operação',
            'parent': 'Conta Pai (Opcional)'
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Despesa - Energia Elétrica'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 4.01.01'}),
            'operation_type': forms.Select(attrs={'class': 'form-select'}),
            # Usar um select para o campo parent, garantindo que a própria conta não seja selecionável como pai
            'parent': forms.Select(attrs={'class': 'form-select'}), 
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Permite selecionar a si mesmo como pai se estiver editando
        queryset = ChartOfAccounts.objects.all().order_by('code')
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        # Define o queryset para o campo parent (Conta Pai)
        self.fields['parent'].queryset = queryset
        # Torna o campo parent opcional na visualização do formulário
        self.fields['parent'].required = False