from django import forms
from .models import Employee
from parties.models import Entity
from django.contrib.auth import get_user_model

User = get_user_model()

class EmployeeForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtra o dropdown de Entidades:
        # 1. Mostra apenas Pessoas Físicas
        # 2. Esconde pessoas que JÁ SÃO funcionários
        queryset = Entity.objects.filter(tipo_entidade='FISICA')
        
        if self.instance and self.instance.pk:
            # Se estiver editando, permite manter a entidade atual
            queryset = queryset | Entity.objects.filter(pk=self.instance.entidade_id)
        else:
            # Se estiver criando, esconde quem já tem vínculo
            queryset = queryset.exclude(colaborador_profile__isnull=False)
            
        self.fields['entidade'].queryset = queryset

    class Meta:
        model = Employee
        fields = [
            'entidade', 'usuario_sistema', 'cargo', 
            'comissao_base_percentual', 'ativo'
        ]
        labels = {
            'entidade': 'Pessoa (Cadastro Principal)',
            'usuario_sistema': 'Usuário de Login (Opcional)',
            'cargo': 'Cargo (Ex: Vendedor)',
            'comissao_base_percentual': 'Comissão Padrão (%)',
            'ativo': 'Ativo no Sistema'
        }
        widgets = {
            'entidade': forms.Select(attrs={'class': 'form-select'}),
            'usuario_sistema': forms.Select(attrs={'class': 'form-select'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'comissao_base_percentual': forms.NumberInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }