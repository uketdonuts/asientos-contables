from django import forms
from django.core.exceptions import ValidationError
from .models import PlanCuenta, Cuenta
from perfiles.models import Perfil
from empresas.models import Empresa

class PlanCuentaForm(forms.ModelForm):
    """Formulario para Plan de Cuentas"""
    class Meta:
        model = PlanCuenta
        fields = ['empresa', 'perfil', 'descripcion']
        widgets = {
            'empresa': forms.Select(),
            'perfil': forms.Select(),
            'descripcion': forms.TextInput(attrs={'placeholder':'Descripción','maxlength':'255'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['empresa'].queryset = Empresa.objects.filter(activa=True)
        self.fields['perfil'].queryset = Perfil.objects.all()
        for field in ['empresa', 'perfil', 'descripcion']:
            self.fields[field].required = True





class CuentaForm(forms.ModelForm):
    """Formulario para Cuentas"""
    class Meta:
        model = Cuenta
        fields = ['cuenta', 'descripcion', 'plan_cuentas', 'cuenta_madre', 'grupo']
        widgets = {
            'cuenta': forms.TextInput(attrs={'placeholder':'Código','maxlength':'14'}),
            'descripcion': forms.TextInput(attrs={'placeholder':'Descripción','maxlength':'255'}),
            'plan_cuentas': forms.Select(),
            'cuenta_madre': forms.Select(),
            'grupo': forms.NumberInput(attrs={'placeholder':'Grupo (1-5)'}),
        }
        labels = {
            'cuenta': 'Código de Cuenta',
            'descripcion': 'Descripción de la Cuenta',
            'plan_cuentas': 'Plan de Cuentas',
            'cuenta_madre': 'Cuenta Madre',
            'grupo': 'Grupo Contable',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['plan_cuentas'].queryset = PlanCuenta.objects.all()
        self.fields['cuenta_madre'].queryset = Cuenta.objects.none()
        if 'plan_cuentas' in self.data:
            try:
                plan_id = int(self.data.get('plan_cuentas'))
                self.fields['cuenta_madre'].queryset = Cuenta.objects.filter(plan_cuentas=plan_id).order_by('cuenta')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.plan_cuentas:
            self.fields['cuenta_madre'].queryset = Cuenta.objects.filter(
                plan_cuentas=self.instance.plan_cuentas
            ).exclude(pk=self.instance.pk).order_by('cuenta')
        for field in ['cuenta', 'descripcion', 'plan_cuentas']:
            self.fields[field].required = True
        for field in ['cuenta_madre', 'grupo']:
            self.fields[field].required = False

    def clean_grupo(self):
        grupo = self.cleaned_data.get('grupo')
        if grupo is not None and (grupo < 1 or grupo > 5):
            raise ValidationError('El grupo debe estar entre 1 y 5.')
        return grupo

    def clean_cuenta_madre(self):
        madre = self.cleaned_data.get('cuenta_madre')
        plan = self.cleaned_data.get('plan_cuentas')
        if madre:
            if madre == self.instance:
                raise ValidationError('Una cuenta no puede ser su propia cuenta madre.')
            if plan and madre.plan_cuentas != plan:
                raise ValidationError('La cuenta madre debe pertenecer al mismo plan.')
        return madre

    def clean(self):
        return super().clean()