from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
import hashlib


class SecureAccessForm(forms.Form):
    """Formulario de acceso ultra-seguro"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña de Acceso Seguro',
            'autocomplete': 'off'
        }),
        label="Contraseña de Acceso"
    )
    
    verification_code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000000',
            'autocomplete': 'off',
            'pattern': '[0-9]{6}'
        }),
        label="Código 2FA (Email)"
    )
    
    app_verification_code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000000',
            'autocomplete': 'off',
            'pattern': '[0-9]{6}'
        }),
        label="Código 2FA (Authenticator App)"
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        
        if not password:
            raise ValidationError("La contraseña es requerida")
        
        # Validar que el usuario sea el autorizado
        if not self.user or self.user.email != 'c.rodriguez@figbiz.net':
            raise ValidationError("Acceso no autorizado para este usuario")
        
        return cleaned_data
    
    def get_password_hash(self):
        """Genera hash seguro de la contraseña"""
        password = self.cleaned_data.get('password', '')
        return hashlib.sha256(password.encode()).hexdigest()


class SecureDataEditForm(forms.Form):
    """Formulario para editar datos en la matriz segura"""
    cell_value = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'off'
        }),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        self.row = kwargs.pop('row', 0)
        self.col = kwargs.pop('col', 0)
        super().__init__(*args, **kwargs)
