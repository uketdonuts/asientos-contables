from django import forms
from .models import Perfil

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['empresa', 'secuencial', 'descripcion', 'vigencia']
        widgets = {
            'empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'secuencial': forms.NumberInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'vigencia': forms.TextInput(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'empresa': {'required': 'La empresa es requerida'},
            'secuencial': {'required': 'El secuencial es requerido'},
        }