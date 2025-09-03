from django import forms
from .models import AsientoDetalle
from asientos.models import Asiento
from plan_cuentas.models import Cuenta
from empresas.models import Empresa
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError

class AsientoDetalleForm(forms.ModelForm):
    class Meta:
        model = AsientoDetalle
        fields = ['asiento', 'cuenta', 'valor', 'polaridad', 'empresa_id']
        widgets = {
            'asiento': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500'
            }),
            'cuenta': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500'
            }),
            'valor': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500',
                'step': '0.01',
                'min': '0'
            }),
            'polaridad': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500'
            }),
            'empresa_id': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500'
            }),
        }
        labels = {
            'asiento': 'Asiento Contable',
            'cuenta': 'Cuenta Contable',
            'valor': 'Monto',
            'polaridad': 'Polaridad',
            'empresa_id': 'Empresa',
        }
        help_texts = {
            'asiento': 'Seleccione el asiento contable al que pertenece este detalle',
            'cuenta': 'Seleccione la cuenta contable',
            'valor': 'Ingrese el monto del movimiento',
            'polaridad': 'Seleccione si es Debe (+) o Haber (-)',
            'empresa_id': 'Seleccione la empresa',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar las opciones de polaridad
        self.fields['polaridad'].choices = [
            ('+', 'Debe'),
            ('-', 'Haber'),
        ]
        
        # Configurar querysets
        self.fields['asiento'].queryset = Asiento.objects.all().order_by('-fecha', 'descripcion')
        self.fields['cuenta'].queryset = Cuenta.objects.all().order_by('codigocuenta')
        self.fields['empresa_id'].queryset = Empresa.objects.all().order_by('nombre')
        
        # Si es una edición, filtrar por empresa del asiento
        if self.instance and self.instance.pk and self.instance.asiento:
            empresa = self.instance.asiento.empresa
            if empresa:
                self.fields['cuenta'].queryset = Cuenta.objects.filter(empresa_id=empresa).order_by('codigocuenta')
    
    def clean(self):
        cleaned_data = super().clean()
        valor = cleaned_data.get('valor')
        polaridad = cleaned_data.get('polaridad')
        asiento = cleaned_data.get('asiento')
        cuenta = cleaned_data.get('cuenta')
        empresa = cleaned_data.get('empresa_id')
        
        # Validar que el valor sea positivo
        if valor is not None and valor <= 0:
            raise forms.ValidationError({
                'valor': 'El monto debe ser mayor a cero.'
            })
        
        # Validar que la cuenta pertenezca a la empresa del asiento
        if asiento and cuenta and empresa:
            if cuenta.empresa_id != empresa:
                raise forms.ValidationError({
                    'cuenta': 'La cuenta seleccionada no pertenece a la empresa del asiento.'
                })
        
        return cleaned_data

class BaseAsientoDetalleInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        if any(self.errors):
            return

        total_debe = 0
        total_haber = 0

        for form in self.forms:
            if not form.is_valid() or form.cleaned_data.get('DELETE'):
                continue

            valor = form.cleaned_data.get('valor', 0) or 0
            polaridad = form.cleaned_data.get('polaridad')

            if polaridad == '+':
                total_debe += valor
            elif polaridad == '-':
                total_haber += valor

        # Validar que debe = haber
        if total_debe != total_haber:
            raise ValidationError(
                f"La suma de los montos debe ser igual al haber. Debe: ${total_debe:.2f}, Haber: ${total_haber:.2f}"
            )