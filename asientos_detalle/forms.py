from django import forms
from .models import AsientoDetalle
from plan_cuentas.models import PlanCuenta
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError

class AsientoDetalleForm(forms.ModelForm):
    hash_transaccion = forms.CharField(disabled=True, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = AsientoDetalle
        fields = ['tipo_cuenta', 'cuenta', 'DetalleDeCausa', 'Referencia', 'valor', 'polaridad']
        widgets = {
            'tipo_cuenta': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_cuenta'}),
            'cuenta': forms.Select(attrs={'class': 'form-select select2', 'id': 'id_cuenta'}),
            'DetalleDeCausa': forms.TextInput(attrs={'class': 'form-control'}),
            'Referencia': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'polaridad': forms.RadioSelect(attrs={'class': 'form-check-input', 'readonly': 'readonly'}),
        }
        error_messages = {
            'tipo_cuenta': {'required': 'El tipo de cuenta es requerido'},
            'cuenta': {'required': 'La cuenta es requerida'},
            'valor': {'required': 'El valor es requerido'},
            'polaridad': {'required': 'La polaridad es requerida'},
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configuramos el queryset para el campo cuenta
        self.fields['cuenta'].queryset = PlanCuenta.objects.all()
        
        # Establecer el valor del hash de transacción (id del asiento)
        if self.instance and self.instance.asiento:
            self.fields['hash_transaccion'].initial = self.instance.asiento.id
            # Filter cuenta by asiento.empresa
            self.fields['cuenta'].queryset = PlanCuenta.objects.filter(empresa=self.instance.asiento.empresa)

        # Establecemos valores predeterminados para polaridad según el tipo de cuenta
        if 'tipo_cuenta' in self.data:
            if self.data['tipo_cuenta'] == 'HABER':
                self.initial['polaridad'] = '-' # Corrected: Was '+'
                self.fields['polaridad'].widget.attrs['disabled'] = True
            elif self.data['tipo_cuenta'] == 'DEBE':
                self.initial['polaridad'] = '+' # Corrected: Was '-'
                self.fields['polaridad'].widget.attrs['disabled'] = True
        elif self.instance and self.instance.tipo_cuenta:
            # También establecemos valores cuando se edita un detalle existente
            if self.instance.tipo_cuenta == 'HABER':
                self.initial['polaridad'] = '-' # Corrected: Was '+'
                self.fields['polaridad'].widget.attrs['disabled'] = True
            elif self.instance.tipo_cuenta == 'DEBE':
                self.initial['polaridad'] = '+' # Corrected: Was '-'
                self.fields['polaridad'].widget.attrs['disabled'] = True
        
        # Asegurar que polaridad sea solo de lectura
        self.fields['polaridad'].widget.attrs['readonly'] = True
    
    def clean(self):
        cleaned_data = super().clean()
        valor = cleaned_data.get('valor')
        tipo_cuenta = cleaned_data.get('tipo_cuenta')
        
        # Validate that a value is provided
        if not valor:
            raise forms.ValidationError("Debe ingresar un valor.")
        
        # Establecer la polaridad automáticamente según el tipo de cuenta
        if tipo_cuenta == 'HABER':
            cleaned_data['polaridad'] = '-' # Corrected: Was '+'
        elif tipo_cuenta == 'DEBE':
            cleaned_data['polaridad'] = '+' # Corrected: Was '-'
            
        return cleaned_data

class BaseAsientoDetalleInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        if any(self.errors):
            # Don't bother validating the sum if individual forms have errors
            return

        current_formset_sum = 0
        forms_to_consider_count = 0

        for form in self.forms:
            if not form.is_valid() or not form.has_changed() and not form.instance.pk:
                # Skip forms that are not valid, or unchanged new forms.
                # For existing forms (form.instance.pk is not None), even if unchanged, they contribute to the sum.
                if form.instance.pk: # Existing, unchanged form
                    if form.instance.valor is not None:
                        forms_to_consider_count +=1
                        if form.instance.polaridad == '+':
                            current_formset_sum += form.instance.valor
                        elif form.instance.polaridad == '-':
                            current_formset_sum -= form.instance.valor
                continue

            if form.cleaned_data.get('DELETE'):
                continue

            forms_to_consider_count += 1
            valor = form.cleaned_data.get('valor', 0) or 0
            polaridad = form.cleaned_data.get('polaridad') # Use polaridad from cleaned_data

            if polaridad == '+': # DEBE
                current_formset_sum += valor
            elif polaridad == '-': # HABER
                current_formset_sum -= valor
        
        # self.instance is the parent Asiento model instance
        if not self.instance.pk:  # New Asiento
            if forms_to_consider_count > 0 and current_formset_sum != 0:
                raise ValidationError(
                    "La suma de los detalles iniciales (debe y haber) debe ser cero para un nuevo asiento."
                )
        else:  # Existing Asiento
            # Calculate sum of details NOT in this formset (i.e., already existing in DB and not being modified/deleted by this formset)
            other_details_sum = 0
            pks_in_formset = {f.instance.pk for f in self.forms if f.instance and f.instance.pk}
            
            # Query details related to the parent Asiento instance, excluding those managed by the current formset
            # (unless they were marked for deletion, in which case they shouldn't be summed).
            for detalle in self.instance.detalles.all():
                is_deleted_in_formset = False
                is_modified_in_formset = False

                for form in self.forms:
                    if form.instance.pk == detalle.pk:
                        is_modified_in_formset = True
                        if form.cleaned_data and form.cleaned_data.get('DELETE'):
                            is_deleted_in_formset = True
                        break # Found the corresponding form

                if not is_modified_in_formset and not is_deleted_in_formset: # It's an existing detail not touched by formset
                    if detalle.valor is not None:
                        if detalle.polaridad == '+':
                            other_details_sum += detalle.valor
                        elif detalle.polaridad == '-':
                            other_details_sum -= detalle.valor
            
            final_total = current_formset_sum + other_details_sum
            if final_total != 0:
                raise ValidationError(
                    f"La suma total de los movimientos (debe y haber) para el asiento debe ser cero (actual: {final_total})."
                )