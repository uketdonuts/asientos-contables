from django import forms
from .models import Perfil

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm',
                'placeholder': 'Ej: Perfil de Ventas, Perfil de Compras, etc.'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm resize-none',
                'rows': 3,
                'placeholder': 'Descripción detallada del perfil contable'
            }),
        }
        labels = {
            'nombre': 'Nombre del Perfil',
            'descripcion': 'Descripción'
        }
        help_texts = {
            'nombre': 'Nombre identificativo y único para el perfil contable',
            'descripcion': 'Descripción opcional del propósito de este perfil contable'
        }
        error_messages = {
            'nombre': {
                'required': 'El nombre del perfil es requerido',
                'max_length': 'El nombre no puede exceder 64 caracteres'
            }
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make nombre required
        self.fields['nombre'].required = True
        
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            nombre = nombre.strip()
            if not nombre:
                raise forms.ValidationError('El nombre no puede estar vacío')
            
            # Check for duplicates
            existing = Perfil.objects.filter(
                nombre__iexact=nombre
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                raise forms.ValidationError(
                    f'Ya existe un perfil con el nombre "{nombre}"'
                )
        
        return nombre

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get('descripcion')
        if descripcion:
            descripcion = descripcion.strip()
            if not descripcion:
                raise forms.ValidationError('La descripción no puede estar vacía')
            
            # Check for duplicates
            existing = Perfil.objects.filter(
                descripcion__iexact=descripcion
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing.exists():
                raise forms.ValidationError(
                    f'Ya existe un perfil con la descripción "{descripcion}"'
                )
        
        return descripcion