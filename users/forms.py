from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['username'].error_messages['required'] = 'Nombre de usuario es obligatorio'
        self.fields['password1'].error_messages['required'] = 'Contraseña es obligatoria'
        self.fields['password2'].error_messages['required'] = 'Confirmación de contraseña es obligatoria'

class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['username'].error_messages['required'] = 'Nombre de usuario es obligatorio'
        self.fields['password'].error_messages['required'] = 'Contraseña es obligatoria'
        self.error_messages['invalid_login'] = 'Nombre de usuario o contraseña incorrectos'

class PasswordRecoveryForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=254)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].error_messages['required'] = 'Correo electrónico es obligatorio'

class CustomPasswordResetForm(PasswordResetForm):
    class Meta:
        model = User
        fields = ['email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['email'].error_messages['required'] = 'Correo electrónico es obligatorio'

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        label='Código OTP', 
        max_length=6, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el código OTP'}),
        error_messages={'required': 'El código OTP es obligatorio'}
    )
    email = forms.EmailField(widget=forms.HiddenInput())

class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['new_password1'].error_messages['required'] = 'Nueva contraseña es obligatoria'
        self.fields['new_password2'].error_messages['required'] = 'Confirmación de contraseña es obligatoria'

class UserProfileForm(forms.ModelForm):
    """Formulario para editar el perfil de usuario"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }