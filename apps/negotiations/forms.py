from django import forms
from .models import Negotiation
from vehicles.models import Vehicle
from employees.models import Employee

class SaleForm(forms.ModelForm):
    # --- LADO A: SAÍDA (O que a loja vende) ---
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.filter(status='AVAILABLE'),
        label="Veículo Vendido (Saída)",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    sale_value = forms.DecimalField(
        label="Valor de Venda (R$)",
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    # --- LADO B: ENTRADA (O que o cliente dá na troca) ---
    has_trade_in = forms.BooleanField(
        required=False, 
        label="Aceitar veículo na troca?",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'onchange': 'toggleTradeIn(this)'})
    )
    
    # Modelo
    trade_in_brand_name = forms.CharField(
        required=False,
        label="Marca (Troca)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: VW'})
    )
    trade_in_model_name = forms.CharField(
        required=False,
        label="Modelo (Troca)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Gol'})
    )
    # Documentos
    trade_in_plate = forms.CharField(
        required=False,
        label="Placa",
        widget=forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'ABC-1234'})
    )
    trade_in_chassi = forms.CharField(
        required=False,
        label="Chassi",
        widget=forms.TextInput(attrs={'class': 'form-control text-uppercase'})
    )
    trade_in_renavam = forms.CharField(
        required=False,
        label="Renavam",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    # Características
    trade_in_year_fab = forms.IntegerField(
        required=False,
        label="Ano Fab.",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    trade_in_year_model = forms.IntegerField(
        required=False,
        label="Ano Mod.",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    trade_in_color = forms.CharField(
        required=False,
        label="Cor",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    trade_in_fuel_type = forms.ChoiceField(
        required=False,
        label="Combustível",
        choices=Vehicle.FUEL_CHOICES, # Puxa as escolhas do modelo
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    trade_in_mileage = forms.IntegerField(
        required=False,
        label="KM Atual",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    # Valor
    trade_in_value = forms.DecimalField(
        required=False,
        label="Valor Acordado na Troca (R$)",
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Negotiation
        fields = ['customer', 'seller']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'seller': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['seller'].queryset = Employee.objects.filter(ativo=True)
        
    def clean(self):
        cleaned_data = super().clean()
        has_trade_in = cleaned_data.get('has_trade_in')
        
        # Se marcou que tem troca, obriga a preencher os dados essenciais
        if has_trade_in:
            required_fields = [
                'trade_in_brand_name', 'trade_in_model_name', 'trade_in_plate', 
                'trade_in_chassi', 'trade_in_year_fab', 'trade_in_year_model', 
                'trade_in_color', 'trade_in_fuel_type', 'trade_in_mileage', 'trade_in_value'
            ]
            for field in required_fields:
                if not cleaned_data.get(field):
                    # Pega o 'label' do campo para a mensagem de erro
                    label = self.fields[field].label
                    self.add_error(field, f"Campo '{label}' é obrigatório para a troca.")
        
        return cleaned_data