from django import forms
from django.core.exceptions import ValidationError
from .models import PlanCuenta, Cuenta


class PlanCuentaForm(forms.ModelForm):
    """Formulario para Plan de Cuentas"""
    class Meta:
        model = PlanCuenta
        fields = ['empresa', 'perfil', 'descripcion']
        widgets = {
            'empresa': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200',
            }),
            'perfil': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200',
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200',
                'placeholder': 'Descripción del plan de cuentas',
                'maxlength': '255'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Importar aquí para evitar circular imports
        from perfiles.models import Perfil
        from empresas.models import Empresa
        
        # Configurar querysets para campos de selección
        self.fields['perfil'].queryset = Perfil.objects.all()
        self.fields['empresa'].queryset = Empresa.objects.filter(activa=True)
        
        # Configurar campos obligatorios
        self.fields['empresa'].required = True
        self.fields['perfil'].required = True
        self.fields['descripcion'].required = True


class CuentaForm(forms.ModelForm):
    """Formulario para Cuentas"""
    
    class Meta:
        model = Cuenta
        fields = ['cuenta', 'descripcion', 'plan_cuentas', 'cuenta_madre', 'grupo']
        widgets = {
            'cuenta': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all duration-200 font-mono',
                'placeholder': 'Código de la cuenta',
                'maxlength': '14'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200',
                'placeholder': 'Descripción de la cuenta',
                'maxlength': '255'
            }),
            'plan_cuentas': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200',
                'id': 'id_plan_cuentas'
            }),
            'cuenta_madre': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-all duration-200',
                'id': 'id_cuenta_madre'
            }),
            'grupo': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200',
                'placeholder': 'Número del grupo (1-5)'
            }),
        }
        labels = {
            'cuenta': 'Código de Cuenta',
            'descripcion': 'Descripción',
            'cuenta_madre': 'Cuenta Madre',
            'plan_cuentas': 'Plan de Cuentas',
            'grupo': 'Grupo Contable'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar querysets y opciones para selectores
        self.fields['plan_cuentas'].queryset = PlanCuenta.objects.all()
        self.fields['plan_cuentas'].empty_label = "Seleccione un plan de cuentas"
        
        # Inicializar cuenta_madre vacío hasta que se seleccione un plan
        self.fields['cuenta_madre'].queryset = Cuenta.objects.none()
        self.fields['cuenta_madre'].empty_label = "Seleccione una cuenta madre (opcional)"
        
        # Si hay un plan seleccionado, cargar las cuentas disponibles
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
        
        # Configurar campos obligatorios
        self.fields['cuenta'].required = True
        self.fields['descripcion'].required = True
        self.fields['plan_cuentas'].required = True
        
        # Configurar campos opcionales
        self.fields['cuenta_madre'].required = False
        self.fields['grupo'].required = False

    def clean_grupo(self):
        """Validar que grupo sea un entero válido si se proporciona"""
        grupo = self.cleaned_data.get('grupo')
        
        # Si no hay valor, devolver None
        if grupo is None:
            return None
            
        # Si es string vacío o solo espacios, devolver None
        if isinstance(grupo, str):
            if not grupo.strip():
                return None
            try:
                grupo_int = int(grupo.strip())
            except ValueError:
                raise ValidationError('El grupo debe ser un número entero.')
        else:
            # Ya es un entero
            grupo_int = grupo
            
        # Validar rango
        if grupo_int < 1 or grupo_int > 5:
            raise ValidationError('El grupo debe estar entre 1 y 5.')
            
        return grupo_int

    def clean_cuenta_madre(self):
        """Validar que la cuenta madre no sea la misma cuenta"""
        cuenta_madre = self.cleaned_data.get('cuenta_madre')
        plan_cuentas = self.cleaned_data.get('plan_cuentas')
        
        if cuenta_madre:
            # Validar que pertenezca al mismo plan de cuentas
            if cuenta_madre.plan_cuentas != plan_cuentas:
                raise ValidationError('La cuenta madre debe pertenecer al mismo plan de cuentas.')
            
            # Si estamos editando, evitar referencia circular
            if self.instance.pk and cuenta_madre.pk == self.instance.pk:
                raise ValidationError('Una cuenta no puede ser su propia cuenta madre.')
        
        return cuenta_madre

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class PlanCuentaFilterForm(forms.Form):
    """Formulario para filtrar planes de cuentas"""
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200',
            'placeholder': 'Buscar por descripción...'
        })
    )
    
    empresa = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from empresas.models import Empresa
        self.fields['empresa'].queryset = Empresa.objects.filter(activa=True)


class CuentaFilterForm(forms.Form):
    """Formulario para filtrar cuentas contables"""
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200',
            'placeholder': 'Buscar por código o descripción...'
        })
    )
    
    plan_cuentas = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['plan_cuentas'].queryset = PlanCuenta.objects.all()
