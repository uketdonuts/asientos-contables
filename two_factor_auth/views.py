from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django_otp.decorators import otp_required
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice
import qrcode
from io import BytesIO
import base64
from datetime import timedelta
from django.utils import timezone
import binascii
import os
import secrets
import string

def generate_recovery_codes(count=10, length=8):
    """Genera códigos de recuperación alfanuméricos."""
    alphabet = string.ascii_uppercase + string.digits
    # Excluir caracteres ambiguos como I, 1, O, 0
    alphabet = alphabet.replace('I', '').replace('1', '').replace('O', '').replace('0', '')
    
    codes = []
    for _ in range(count):
        # Generar un código de recuperación aleatorio
        code = ''.join(secrets.choice(alphabet) for _ in range(length))
        # Insertar un guion en medio del código para mejor legibilidad
        code = code[:4] + '-' + code[4:]
        codes.append(code)
    
    return codes

class TwoFactorAuthView(View):
    @otp_required
    def get(self, request):
        devices = devices_for_user(request.user)
        return render(request, 'two_factor/two_factor_confirm.html', {'devices': devices})

class TwoFactorAuthSetupView(LoginRequiredMixin, View):
    """Vista para configurar la autenticación de dos factores"""
    
    def get(self, request):
        # Comprobar si el usuario ya tiene un dispositivo configurado
        devices = list(devices_for_user(request.user, confirmed=True))
        
        if devices:
            # Si ya hay dispositivos, mostrar información
            return render(request, 'two_factor/setup_complete.html', {'devices': devices})
        
        # Crear un nuevo dispositivo TOTP si no existe (manejar múltiples pendientes)
        try:
            device, created = TOTPDevice.objects.get_or_create(
                user=request.user,
                confirmed=False,
                defaults={
                    'name': f"Autenticador de {request.user.username}",
                    'tolerance': 20,  # Permitir 20 ventanas de tiempo (±300s = 600s total)
                    'drift': 0       # Sin deriva temporal
                }
            )
        except TOTPDevice.MultipleObjectsReturned:
            device = TOTPDevice.objects.filter(user=request.user, confirmed=False).order_by('-id').first()
            created = False
        
    # Importante: NO regenerar la clave en cada GET.
    # Mantener estable el secreto mientras el dispositivo esté sin confirmar,
    # para que el código del usuario coincida con el que verifica el servidor.
        # Asegurar configuración coherente (sin cambiar la clave ni bajar tolerancia)
        updates = []
        if device.tolerance is None or device.tolerance < 20:
            device.tolerance = 20  # Aumentar tolerancia para dispositivos existentes
            updates.append("tolerance")
        if device.drift is None:
            device.drift = 0
            updates.append("drift")
        if updates:
            device.save(update_fields=updates)

        # Generar el código QR usando la URL oficial del dispositivo (usa bin_key internamente)
        url = device.config_url
        qr = qrcode.make(url)
        buffered = BytesIO()
        qr.save(buffered)
        qr_code = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Obtener la clave en formato Base32 para mostrarla al usuario
        # Derivar secreto Base32 directamente desde bin_key para evitar ambigüedades
        try:
            key_bytes = device.bin_key
        except Exception:
            # Fallback a interpretar como HEX si bin_key no está disponible
            try:
                key_bytes = binascii.unhexlify(device.key.encode())
            except Exception:
                key_bytes = bytes(device.key)
        secret_key = base64.b32encode(key_bytes).decode('utf-8')

        return render(request, 'two_factor/setup.html', {
            'device': device,
            'qr_code': qr_code,
            'secret_key': secret_key
        })
    
    def post(self, request):
        token = request.POST.get('token')
        
        # Intentar obtener un dispositivo no confirmado
        try:
            device = TOTPDevice.objects.get(user=request.user, confirmed=False)
        except TOTPDevice.DoesNotExist:
            messages.error(request, "No se encontró un dispositivo de autenticación pendiente.")
            return redirect('two_factor_auth:setup')
        except TOTPDevice.MultipleObjectsReturned:
            device = TOTPDevice.objects.filter(user=request.user, confirmed=False).order_by('-id').first()
        
        # Validar el token
        if device.verify_token(token):
            # Confirmar el dispositivo si el token es correcto
            device.confirmed = True
            device.save()
            
            # Generar códigos de recuperación
            recovery_codes = generate_recovery_codes()
            
            # Guardar códigos de recuperación en el modelo de usuario
            if hasattr(request.user, 'set_recovery_codes'):
                request.user.set_recovery_codes(recovery_codes)
            
            # Actualizar campo usr_2fa en modelo User SOLO cuando el dispositivo es confirmado
            if hasattr(request.user, 'usr_2fa'):
                request.user.usr_2fa = True
                request.user.save()
            
            # Marcar la sesión como verificada con 2FA
            request.session['2fa_verified'] = True
            
            # Guardar los códigos en la sesión para mostrarlos en la página de configuración completada
            request.session['recovery_codes'] = recovery_codes
                
            messages.success(request, "¡Autenticación de dos factores configurada correctamente!")
            return redirect('two_factor_auth:setup_complete')
        else:
            messages.error(request, "Código incorrecto. Inténtelo de nuevo.")
            return redirect('two_factor_auth:setup')

class TwoFactorAuthVerifyView(LoginRequiredMixin, View):
    """Vista para verificar el código de autenticación de dos factores"""
    
    def get(self, request):
        # Verificar si el usuario realmente tiene 2FA habilitado en la base de datos
        # Esto ayuda a corregir inconsistencias entre dispositivos y la bandera usr_2fa
        if hasattr(request.user, 'usr_2fa') and not request.user.usr_2fa:
            # Si usr_2fa es False en la BD, verificar si hay dispositivos
            devices = list(devices_for_user(request.user, confirmed=True))
            if devices:
                # Hay inconsistencia - eliminar los dispositivos TOTP
                print(f"[DEBUG] Eliminando dispositivos inconsistentes para {request.user.username}")
                TOTPDevice.objects.filter(user=request.user).delete()
                messages.warning(request, "Hemos detectado un problema con tu configuración de 2FA. Por favor, configúrala nuevamente.")
                return redirect('two_factor_auth:setup')
        
        return render(request, 'two_factor/verify.html')
    
    def post(self, request):
        # La misma validación que en el método get
        if hasattr(request.user, 'usr_2fa') and not request.user.usr_2fa:
            devices = list(devices_for_user(request.user, confirmed=True))
            if devices:
                TOTPDevice.objects.filter(user=request.user).delete()
                messages.warning(request, "Hemos detectado un problema con tu configuración de 2FA. Por favor, configúrala nuevamente.")
                return redirect('two_factor_auth:setup')
        
        token = request.POST.get('token')
        
        # Obtener dispositivos del usuario
        devices = list(devices_for_user(request.user, confirmed=True))
        
        if not devices:
            messages.error(request, "No tienes dispositivos de autenticación configurados.")
            return redirect('two_factor_auth:setup')
        
        # Verificar el token en todos los dispositivos
        for device in devices:
            if device.verify_token(token):
                # Marcar la sesión como verificada con 2FA
                request.session['2fa_verified'] = True
                
                # Redirigir a la página objetivo o al inicio
                next_url = request.session.get('next', reverse('home'))
                return redirect(next_url)
        
        messages.error(request, "Código incorrecto. Inténtelo de nuevo.")
        return redirect('two_factor_auth:verify')

class TwoFactorAuthDisableView(LoginRequiredMixin, View):
    """Vista para deshabilitar la autenticación de dos factores"""
    
    def get(self, request):
        devices = list(devices_for_user(request.user, confirmed=True))
        return render(request, 'two_factor/disable.html', {'devices': devices})
    
    def post(self, request):
        confirm = request.POST.get('confirm')
        
        if confirm == 'yes':
            # Eliminar todos los dispositivos TOTP del usuario
            TOTPDevice.objects.filter(user=request.user).delete()
            
            # Actualizar campo usr_2fa en modelo User si existe
            if hasattr(request.user, 'usr_2fa'):
                request.user.usr_2fa = False
                request.user.save()
            
            # Eliminar la verificación de 2FA de la sesión
            if '2fa_verified' in request.session:
                del request.session['2fa_verified']
            
            messages.success(request, "La autenticación de dos factores ha sido deshabilitada.")
            return redirect('home')
        
        return redirect('two_factor_auth:disable')

class TwoFactorAuthSetupCompleteView(LoginRequiredMixin, View):
    """Vista de confirmación de configuración completada"""
    
    def get(self, request):
        devices = list(devices_for_user(request.user, confirmed=True))
        
        # Obtener los códigos de recuperación de la sesión si existen
        recovery_codes = request.session.pop('recovery_codes', None)
        
        # Si no hay códigos en la sesión, intentar obtenerlos del modelo de usuario
        if not recovery_codes and hasattr(request.user, 'get_recovery_codes'):
            recovery_codes = request.user.get_recovery_codes()
        
        return render(request, 'two_factor/setup_complete.html', {
            'devices': devices,
            'recovery_codes': recovery_codes
        })

class TwoFactorAuthTransitionView(LoginRequiredMixin, View):
    """Vista para el período de transición de 2FA para usuarios existentes"""
    
    def get(self, request):
        # Comprobar si el usuario ya tiene 2FA configurado
        has_devices = bool(list(devices_for_user(request.user, confirmed=True)))
        
        # Si ya tiene 2FA, redirigir a la página principal
        if has_devices:
            request.user.usr_2fa = True
            request.user.save()
            messages.success(request, "Ya tienes la autenticación de dos factores configurada.")
            return redirect('home')
        
        # Calcular fecha límite (7 días desde hoy)
        grace_period_end = timezone.now() + timedelta(days=7)
        grace_period_end_str = grace_period_end.strftime('%d/%m/%Y')
        
        # Guardar la fecha límite en la sesión
        request.session['2fa_grace_period_end'] = grace_period_end.isoformat()
        
        return render(request, 'two_factor/transition.html', {
            'grace_period_end': grace_period_end_str
        })
    
    def post(self, request):
        action = request.POST.get('action')
        
        if action == 'configure_now':
            # Redirigir a la página de configuración de 2FA
            return redirect('two_factor_auth:setup')
        elif action == 'remind_later':
            # Marcar recordatorio para mostrar de nuevo en el próximo inicio de sesión
            messages.info(request, "Te recordaremos configurar la autenticación de dos factores en tu próximo inicio de sesión.")
            return redirect('home')
        
        return redirect('two_factor_auth:transition')

class TwoFactorAuthRecoveryView(LoginRequiredMixin, View):
    """Vista para verificar usando códigos de recuperación"""
    
    def get(self, request):
        # Verificar si el usuario realmente tiene 2FA habilitado
        if not hasattr(request.user, 'usr_2fa') or not request.user.usr_2fa:
            messages.warning(request, "No tienes habilitada la autenticación de dos factores.")
            return redirect('home')
        
        return render(request, 'two_factor/recovery.html')
    
    def post(self, request):
        recovery_code = request.POST.get('recovery_code', '').strip()
        
        # Verificar si el usuario tiene códigos de recuperación
        if not hasattr(request.user, 'get_recovery_codes'):
            messages.error(request, "No se pudieron recuperar tus códigos de recuperación.")
            return redirect('two_factor_auth:verify')
        
        recovery_codes = request.user.get_recovery_codes()
        
        if not recovery_codes:
            messages.error(request, "No tienes códigos de recuperación configurados.")
            return redirect('two_factor_auth:verify')
        
        # Verificar el código de recuperación
        if recovery_code in recovery_codes:
            # Marcar la sesión como verificada con 2FA
            request.session['2fa_verified'] = True
            
            # Eliminar el código usado
            recovery_codes.remove(recovery_code)
            request.user.set_recovery_codes(recovery_codes)
            
            # Mostrar mensaje de advertencia sobre el código usado
            messages.warning(request, 
                "Has iniciado sesión con un código de recuperación. Este código ya no es válido. "
                "Te quedan {} códigos de recuperación.".format(len(recovery_codes)))
            
            # Redirigir a la página objetivo o al inicio
            next_url = request.session.get('next', reverse('home'))
            return redirect(next_url)
        
        messages.error(request, "Código de recuperación incorrecto. Inténtalo de nuevo.")
        return redirect('two_factor_auth:recovery')
