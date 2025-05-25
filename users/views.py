from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.views import PasswordResetView
from django.views.generic import FormView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import (
    CustomUserCreationForm, 
    CustomPasswordResetForm, 
    CustomAuthenticationForm,
    OTPVerificationForm,
    CustomSetPasswordForm,
    UserProfileForm
)
from django.urls import reverse_lazy
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.core.mail import send_mail
from django.http import HttpResponse
from django.conf import settings
import logging
import traceback
import random
import string
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages

# Configurar logging
logger = logging.getLogger(__name__)

# Dynamically get the custom user model
User = get_user_model()

# Almacén temporal para códigos OTP y sus tiempos de expiración
# Formato: {'email': {'otp': '123456', 'expiry': datetime_obj}}
OTP_STORE = {}

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registro exitoso. Ahora debes configurar la autenticación de dos factores.")
            return redirect('two_factor_auth:setup')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                print(f"\n[DEBUG] login_view - Usuario autenticado: {user.username}")
                login(request, user)
                
                # Verificar si hay dispositivos confirmados
                devices = list(devices_for_user(user, confirmed=True))
                has_devices = bool(devices)
                print(f"[DEBUG] Usuario tiene dispositivos 2FA confirmados: {has_devices}")
                print(f"[DEBUG] Dispositivos encontrados: {len(devices)}")
                
                # Verificar el valor de usr_2fa para detectar inconsistencias
                usr_2fa_value = getattr(user, 'usr_2fa', None)
                print(f"[DEBUG] Valor de usr_2fa en BD: {usr_2fa_value}")
                
                # Si hay inconsistencia entre usr_2fa y los dispositivos, corregir
                if has_devices and hasattr(user, 'usr_2fa') and not user.usr_2fa:
                    print(f"[DEBUG] Eliminando dispositivos inconsistentes para {user.username}")
                    # Hay una inconsistencia, eliminar los dispositivos
                    TOTPDevice.objects.filter(user=user).delete()
                    has_devices = False
                
                # Si no tiene 2FA configurado, redirigir a la configuración SIN MENSAJE
                # (el mensaje lo pondrá el middleware)
                if not has_devices:
                    print("[DEBUG] Redirigiendo a setup por falta de dispositivos confirmados")
                    return redirect('two_factor_auth:setup')
                
                # Guardamos la preferencia del usuario en la sesión para redireccionar después de 2FA
                if user.is_superuser:
                    request.session['next'] = '/admin/'
                    print("[DEBUG] Guardando ruta de admin en sesión")
                else:
                    request.session['next'] = reverse('entries:entry_list')
                    print("[DEBUG] Guardando ruta de entries en sesión")
                
                # Primero se debe verificar 2FA antes de redirigir al destino deseado
                print("[DEBUG] Redirigiendo a verify desde login_view")
                return redirect('two_factor_auth:verify')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def password_reset_complete_view(request):
    return render(request, 'users/password_reset_complete.html')

def create_or_get_totp_device(user):
    """Crea o obtiene un dispositivo TOTP para el usuario."""
    # Buscar dispositivos existentes
    devices = TOTPDevice.objects.devices_for_user(user)
    
    # Si ya existe un dispositivo, devolverlo
    for device in devices:
        if isinstance(device, TOTPDevice) and device.confirmed:
            print(f"Dispositivo TOTP existente encontrado para {user.username}")
            return device
    
    # Si no existe, crear uno nuevo
    device = TOTPDevice.objects.create(user=user, name=f"totp_{user.username}", confirmed=True)
    print(f"Nuevo dispositivo TOTP creado para {user.username}")
    return device

def generate_otp_code(length=6):
    """Genera un código OTP numérico de la longitud especificada."""
    return ''.join(random.choices(string.digits, k=length))

class CustomPasswordResetView(FormView):
    form_class = CustomPasswordResetForm
    template_name = 'users/password_reset.html'
    success_url = reverse_lazy('users:verify_otp')

    def form_valid(self, form):
        email = form.cleaned_data.get('email')
        users = User.objects.filter(email=email)
        user = users.first()
        
        if user:
            print(f"Usuario encontrado con email: {email}")
            
            # Asegurar que el usuario tenga un dispositivo TOTP
            device = create_or_get_totp_device(user)
            
            if device:
                # Generar OTP y establecer tiempo de expiración (10 minutos)
                otp_code = generate_otp_code()
                expiry_time = timezone.now() + timedelta(minutes=10)
                
                # Almacenar OTP y tiempo de expiración en nuestro almacén temporal
                OTP_STORE[email] = {
                    'otp': otp_code,
                    'expiry': expiry_time,
                    'user_id': user.usr_id
                }
                
                print(f"Token OTP generado: {otp_code}, válido hasta: {expiry_time}")
                
                
                # Asegurar que el correo del usuario es válido
                if not user.email:
                    print(f"❌ El usuario {user.username} no tiene un correo electrónico configurado")
                    return redirect(self.success_url)
                
                # Enviar correo con OTP
                try:
                    print("Intentando enviar correo con código OTP...")
                    
                    # Crear el mensaje de correo
                    subject = 'Su código OTP para restablecer la contraseña'
                    message = (f'Su código OTP para restablecer la contraseña es: {otp_code}\n'
                              f'Este código es válido por 10 minutos.')
                    from_email = settings.DEFAULT_FROM_EMAIL
                    to_email = user.email
                    
                    # Enviar el correo
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=from_email,
                        recipient_list=[to_email],
                        fail_silently=False,
                    )
                    print(f"✅ Correo enviado exitosamente a {to_email}")
                    
                except Exception as e:
                    print(f"❌ Error al enviar correo: {str(e)}")
                    print(traceback.format_exc())
            
            # Guardar email en la sesión para pasarlo a la vista de verificación
            self.request.session['reset_email'] = email
        
        return super().form_valid(form)

class OTPVerificationView(FormView):
    form_class = OTPVerificationForm
    template_name = 'users/verify_otp.html'
    success_url = reverse_lazy('users:set_new_password')
    
    def get_initial(self):
        initial = super().get_initial()
        # Obtener el email de la sesión
        email = self.request.session.get('reset_email', '')
        initial['email'] = email
        return initial
    
    def form_valid(self, form):
        otp_code = form.cleaned_data.get('otp')
        email = form.cleaned_data.get('email')
        
        # Verificar si el email tiene un OTP almacenado
        if email in OTP_STORE:
            stored_data = OTP_STORE[email]
            stored_otp = stored_data.get('otp')
            expiry_time = stored_data.get('expiry')
            user_id = stored_data.get('user_id')
            
            # Verificar si el código OTP es válido y no ha expirado
            if stored_otp == otp_code and expiry_time and timezone.now() < expiry_time:
                # Código válido y no expirado
                # Guardar el usuario en la sesión para la siguiente vista
                self.request.session['reset_user_id'] = user_id
                return super().form_valid(form)
        
        # Si llegamos aquí, el código OTP no es válido o ha expirado
        form.add_error('otp', 'Código OTP incorrecto o expirado')
        return self.form_invalid(form)

class SetNewPasswordView(FormView):
    form_class = CustomSetPasswordForm
    template_name = 'users/set_new_password.html'
    success_url = reverse_lazy('users:password_reset_complete')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Obtener el usuario de la sesión
        user_id = self.request.session.get('reset_user_id')
        if user_id:
            try:
                user = User.objects.get(usr_id=user_id)
                kwargs['user'] = user
            except User.DoesNotExist:
                pass
        return kwargs
    
    def form_valid(self, form):
        # Actualizar la contraseña
        form.save()
        
        # Limpiar datos de la sesión y OTP_STORE
        email = self.request.session.get('reset_email')
        if email and email in OTP_STORE:
            del OTP_STORE[email]
            
        if 'reset_email' in self.request.session:
            del self.request.session['reset_email']
        if 'reset_user_id' in self.request.session:
            del self.request.session['reset_user_id']
        
        messages.success(self.request, 'Tu contraseña ha sido actualizada correctamente.')
        return super().form_valid(form)

class PerfilUsuarioView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar el perfil del usuario actual"""
    template_name = 'users/perfil.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        # Puedes agregar más datos al contexto si es necesario
        return context

class EditarPerfilUsuarioView(LoginRequiredMixin, View):
    """Vista para editar el perfil del usuario actual"""
    
    def get(self, request):
        form = UserProfileForm(instance=request.user)
        return render(request, 'users/editar_perfil.html', {'form': form})
    
    def post(self, request):
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Tu perfil ha sido actualizado correctamente.")
            return redirect('users:perfil')
        return render(request, 'users/editar_perfil.html', {'form': form})