from django import forms
from .models import Vehicle

class VehicleAcquisitionForm(forms.ModelForm):
    # Campos extras que não estão no modelo Vehicle, mas precisamos para o Service
    seller_name = forms.CharField(label="Nome do Vendedor", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    seller_document = forms.CharField(label="CPF/CNPJ Vendedor", max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Vehicle
        fields = [
            'model', 'chassi', 'plate', 'renavam',
            'year_fab', 'year_model', 'color', 'fuel_type', 'mileage',
            'acquisition_cost', 'sale_price', 'notes'
        ]
        widgets = {
            'model': forms.Select(attrs={'class': 'form-select'}), # Ideal seria autocomplete
            'chassi': forms.TextInput(attrs={'class': 'form-control text-uppercase'}),
            'plate': forms.TextInput(attrs={'class': 'form-control text-uppercase'}),
            'renavam': forms.TextInput(attrs={'class': 'form-control'}),
            'year_fab': forms.NumberInput(attrs={'class': 'form-control'}),
            'year_model': forms.NumberInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'fuel_type': forms.Select(attrs={'class': 'form-select'}),
            'mileage': forms.NumberInput(attrs={'class': 'form-control'}),
            'acquisition_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'sale_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_seller_document(self):
        # Remove pontos e traços
        doc = self.cleaned_data['seller_document']
        return ''.join(filter(str.isdigit, doc))
    

# ... (imports anteriores)

class VehicleEditForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        # Apenas campos seguros para edição cadastral
        fields = [
            'model', 'plate', 'chassi', 'renavam',
            'year_fab', 'year_model', 'color', 'fuel_type', 
            'mileage', 'status', 'sale_price', 'notes'
        ]
        widgets = {
            'model': forms.Select(attrs={'class': 'form-select'}),
            'plate': forms.TextInput(attrs={'class': 'form-control text-uppercase'}),
            'chassi': forms.TextInput(attrs={'class': 'form-control text-uppercase'}),
            'renavam': forms.TextInput(attrs={'class': 'form-control'}),
            'year_fab': forms.NumberInput(attrs={'class': 'form-control'}),
            'year_model': forms.NumberInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'fuel_type': forms.Select(attrs={'class': 'form-select'}),
            'mileage': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}), # Permitimos ajuste manual de status se necessário
            'sale_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }