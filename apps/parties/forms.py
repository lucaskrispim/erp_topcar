from django import forms
from .models import Entity

class EntityForm(forms.ModelForm):
    class Meta:
        model = Entity
        fields = [
            'nome_razao_social', 'documento_principal', 'tipo_entidade',
            'email', 'telefone'
        ]
        labels = {
            'nome_razao_social': 'Nome / Razão Social',
            'documento_principal': 'CPF / CNPJ',
            'tipo_entidade': 'Tipo de Pessoa'
        }
        widgets = {
            'nome_razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'documento_principal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apenas números'}),
            'tipo_entidade': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
    def clean_documento_principal(self):
        # Limpa máscara (pontos, traços) antes de salvar
        doc = self.cleaned_data['documento_principal']
        return ''.join(filter(str.isdigit, doc))