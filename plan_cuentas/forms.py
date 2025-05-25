from django import forms
from .models import PlanCuenta
from perfiles.models import Perfil

class PlanCuentaForm(forms.ModelForm):
    class Meta:
        model = PlanCuenta
        fields = ['empresa', 'perfil', 'grupo', 'codigocuenta', 'descripcion', 'cuentamadre']
        widgets = {
            'empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'perfil': forms.Select(attrs={'class': 'form-select select2'}),
            'grupo': forms.NumberInput(attrs={'class': 'form-control'}),
            'codigocuenta': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cuentamadre': forms.TextInput(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'empresa': {'required': 'La empresa es requerida'},
            'grupo': {'required': 'El grupo es requerido'},
            'codigocuenta': {'required': 'El código de cuenta es requerido'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar solo perfiles vigentes en el selector
        self.fields['perfil'].queryset = Perfil.objects.filter(vigencia='S')