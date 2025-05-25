from django import forms
from .models import Asiento
from perfiles.models import Perfil

class AsientoForm(forms.ModelForm):
    class Meta:
        model = Asiento
        fields = ['fecha', 'perfil']
        widgets = {
            'perfil': forms.Select(attrs={'class': 'form-select select2'}),
        }
        error_messages = {
            'fecha': {'required': 'La fecha es requerida'},
            'perfil': {'required': 'El perfil contable es requerido'},
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter active profiles
        self.fields['perfil'].queryset = Perfil.objects.filter(vigencia='S')
        
        # Add user to form fields for later use in save
        self.user = user
    
    def clean(self):
        cleaned_data = super().clean()
        # Instance is available in self.instance
        asiento = self.instance

        # This validation is for forms that might be saved without going through the model's save method directly first,
        # or for providing user-friendly form errors.
        # It assumes details are managed in a way that they can be accessed here, e.g., through a formset.
        # If details are not yet associated with the asiento instance (e.g., new asiento with details added in same request),
        # this check might need to be adjusted or primarily rely on the model's save method validation.

        # For existing asientos, or if details are already linked (e.g. via formset)
        if asiento.pk: # Condition simplified: if asiento.pk is true, hasattr(asiento, 'detalles') is implied for a standard setup.
            total_movimientos = 0
            for detalle in asiento.detalles.all():
                if detalle.valor is not None:
                    if detalle.polaridad == '+':
                        total_movimientos += detalle.valor
                    elif detalle.polaridad == '-':
                        total_movimientos -= detalle.valor
            
            if total_movimientos != 0:
                raise forms.ValidationError(
                    "La suma de los movimientos (debe y haber) debe ser igual a cero para guardar el asiento."
                )
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.usuario_creacion = self.user
        if commit:
            instance.save()
        return instance