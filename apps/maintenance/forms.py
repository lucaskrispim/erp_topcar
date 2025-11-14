from django import forms
from .models import ServiceOrder, ServiceOrderItem
from vehicles.models import Vehicle
from parties.models import Entity

class ServiceOrderCreateForm(forms.ModelForm):
    # Filtra apenas Fornecedores (Pessoas ou Empresas)
    supplier = forms.ModelChoiceField(
        queryset=Entity.objects.all(), # Idealmente filtrar por papel 'FORNECEDOR' se tivesse
        label="Fornecedor / Oficina",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Filtra veículos que NÃO estão vendidos
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.exclude(status='SOLD'),
        label="Veículo",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = ServiceOrder
        fields = ['vehicle', 'supplier', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ServiceOrderItemForm(forms.ModelForm):
    class Meta:
        model = ServiceOrderItem
        fields = ['description', 'category', 'cost']
        labels = {
            'description': 'Descrição do Item/Serviço',
            'category': 'Categoria',
            'cost': 'Custo (R$)'
        }
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control'}),
        }