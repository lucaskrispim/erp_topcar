from django import forms
from .models import Negotiation
from vehicles.models import Vehicle
from parties.models import Entity
from employees.models import Employee

class SaleForm(forms.ModelForm):
    # Campos virtuais para selecionar o carro e valor (serão usados para criar o Item)
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.filter(status='AVAILABLE'),
        label="Veículo para Venda",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    sale_value = forms.DecimalField(
        label="Valor Fechado (R$)",
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Negotiation
        fields = ['customer', 'seller'] # O resto o sistema preenche
        labels = {
            'customer': 'Cliente Comprador',
            'seller': 'Vendedor Responsável'
        }
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'seller': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra apenas Clientes (PF/PJ) e Funcionários Ativos
        # Nota: Idealmente você teria um filtro 'role' na Entity, mas vamos simplificar
        self.fields['seller'].queryset = Employee.objects.filter(ativo=True)