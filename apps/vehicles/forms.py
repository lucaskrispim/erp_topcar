from django import forms
from .models import Vehicle, Brand, Model

class VehicleAcquisitionForm(forms.ModelForm):
    # Campos extras para Vendedor
    seller_name = forms.CharField(label="Nome do Vendedor", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    seller_document = forms.CharField(label="CPF/CNPJ Vendedor", max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))

    # --- CAMPO NOVO (CUSTOMIZADO) ---
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all().order_by('name'),
        label="Marca",
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            # Atributos HTMX:
            'hx-get': '/vehicles/ajax/load-models/', # A URL que o HTMX chamará
            'hx-trigger': 'change',                  # Dispara no evento 'change'
            'hx-target': '#id_model',                # Onde colocar a resposta (o dropdown de modelo)
            'hx-indicator': '#model-loader'          # Mostra o spinner de "Carregando"
        })
    )

    class Meta:
        model = Vehicle
        # Definimos 'brand' e 'model' na ordem correta
        fields = [
            'brand', 'model', 'chassi', 'plate', 'renavam',
            'year_fab', 'year_model', 'color', 'fuel_type', 'mileage',
            'acquisition_cost', 'sale_price', 'notes'
        ]
        widgets = {
            # 'model' será customizado abaixo no __init__
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

    # --- LÓGICA DO DROPDOWN DEPENDENTE ---
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # O campo 'model' começa com queryset VAZIO
        self.fields['model'].queryset = Model.objects.none()
        self.fields['model'].widget.attrs.update({'class': 'form-select'})

        # Se o formulário foi enviado (POST) ou teve erro de validação
        if 'brand' in self.data:
            try:
                brand_id = int(self.data.get('brand'))
                # Se o form voltou com erro, preenchemos o queryset de modelo
                # para que o valor selecionado anteriormente ainda seja válido.
                self.fields['model'].queryset = Model.objects.filter(brand_id=brand_id).order_by('name')
            except (ValueError, TypeError):
                pass # Mantém o queryset vazio se a marca for inválida

    def clean_seller_document(self):
        doc = self.cleaned_data['seller_document']
        return ''.join(filter(str.isdigit, doc))
    

# ... (imports anteriores)

# --- FORMULÁRIO DE EDIÇÃO (MODIFICADO) ---
class VehicleEditForm(forms.ModelForm):
    # Campo customizado de Marca com HTMX
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all().order_by('name'),
        label="Marca",
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'hx-get': '/vehicles/ajax/load-models/', # Reutiliza a URL do HTMX
            'hx-trigger': 'change',
            'hx-target': '#id_model',
            'hx-indicator': '#model-loader'
        })
    )

    class Meta:
        model = Vehicle
        # Adicionamos 'brand' ao fields
        fields = [
            'brand', 'model', 'plate', 'chassi', 'renavam',
            'year_fab', 'year_model', 'color', 'fuel_type', 
            'mileage', 'status', 'sale_price', 'notes'
        ]
        # Widgets para consistência
        widgets = {
            'plate': forms.TextInput(attrs={'class': 'form-control text-uppercase'}),
            'chassi': forms.TextInput(attrs={'class': 'form-control text-uppercase'}),
            'renavam': forms.TextInput(attrs={'class': 'form-control'}),
            'year_fab': forms.NumberInput(attrs={'class': 'form-control'}),
            'year_model': forms.NumberInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'fuel_type': forms.Select(attrs={'class': 'form-select'}),
            'mileage': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'sale_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    # LÓGICA CRÍTICA DE EDIÇÃO
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) # Carrega o 'instance' (o carro)
        
        self.fields['model'].widget.attrs.update({'class': 'form-select'})

        # self.instance é o veículo que estamos editando (GET)
        if self.instance and self.instance.pk:
            # 1. Pré-seleciona a Marca correta
            if self.instance.model: # Proteção caso modelo seja nulo
                self.fields['brand'].initial = self.instance.model.brand_id
            
                # 2. Pré-popula o queryset de Modelos
                self.fields['model'].queryset = Model.objects.filter(brand_id=self.instance.model.brand_id).order_by('name')
        
        # Lógica para quando o form volta com erro (POST)
        elif 'brand' in self.data:
            try:
                brand_id = int(self.data.get('brand'))
                self.fields['model'].queryset = Model.objects.filter(brand_id=brand_id).order_by('name')
            except (ValueError, TypeError):
                self.fields['model'].queryset = Model.objects.none()
        else:
            self.fields['model'].queryset = Model.objects.none()



class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name']
        labels = {
            'name': 'Nome da Marca'
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Toyota'})
        }


# --- FORMULÁRIO DE MODELOS ---
class ModelForm(forms.ModelForm):
    # Usamos um ModelChoiceField para permitir escolher a Marca
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all().order_by('name'),
        label="Marca",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Model
        fields = ['brand', 'name']
        labels = {
            'name': 'Nome do Modelo'
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Corolla'})
        }