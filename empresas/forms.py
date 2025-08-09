from django import forms
from django.core.exceptions import ValidationError
from .models import Empresa


class EmpresaForm(forms.ModelForm):
    """Formulario para crear y editar empresas"""
    class Meta:
        model = Empresa
        fields = ['nombre', 'type', 'descripcion', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Nombre completo de la empresa',
                'maxlength': '200'
            }),
            'type': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Tipo de empresa (opcional)',
                'maxlength': '50'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none',
                'placeholder': 'Descripción adicional de la empresa (opcional)',
                'rows': 3
            }),
            'activa': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
        }
        labels = {
            'nombre': 'Nombre de la Empresa',
            'type': 'Tipo de Empresa',
            'descripcion': 'Descripción',
            'activa': '¿Empresa Activa?'
        }
        help_texts = {
            'nombre': 'Nombre completo y oficial de la empresa',
            'type': 'Clasificación o tipo de empresa (opcional)',
            'descripcion': 'Información adicional sobre la empresa',
            'activa': 'Marcar si la empresa está activa en el sistema'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar campos obligatorios
        self.fields['nombre'].required = True
        self.fields['type'].required = False
        self.fields['descripcion'].required = False
        
        # Si es creación, marcar como activa por defecto
        if not self.instance.pk:
            self.fields['activa'].initial = True

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not nombre or nombre.strip() == '':
            raise ValidationError('El nombre de la empresa es obligatorio')
        
        nombre = nombre.strip()
        
        # Validar unicidad del nombre
        existing = Empresa.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError('Ya existe una empresa con este nombre')
        
        return nombre

    def clean(self):
        cleaned_data = super().clean()
        
        # Validaciones adicionales si es necesario
        nombre = cleaned_data.get('nombre')
        
        if nombre:
            # Verificar que el nombre no esté vacío después de strip
            if not nombre.strip():
                raise ValidationError('El nombre de la empresa no puede estar vacío')
        
        return cleaned_data


class EmpresaFilterForm(forms.Form):
    """Formulario para filtrar empresas"""
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Buscar por nombre, ID o descripción...'
        })
    )
    
    activa = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todas'),
            ('true', 'Activas'),
            ('false', 'Inactivas')
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    tipo = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Filtrar por tipo...'
        })
    )


class EmpresaSelectForm(forms.Form):
    """Formulario para seleccionar una empresa activa"""
    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.filter(activa=True),
        empty_label="Seleccione una empresa",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        }),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Actualizar queryset para mostrar solo empresas activas
        self.fields['empresa'].queryset = Empresa.objects.filter(activa=True).order_by('nombre')
