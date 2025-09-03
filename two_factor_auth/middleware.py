from django.shortcuts import redirect
from django.urls import reverse, resolve, Resolver404
from django.contrib import messages
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.conf import settings

# Lista de URLs que no requieren verificación de 2FA
EXEMPT_URLS = [
    '/two_factor/setup/',         # Configuración de 2FA
    '/two_factor/setup-complete/', # Confirmación de configuración
    '/two_factor/verify/',        # Verificación de 2FA
    '/users/login/',
    '/users/register/',
    '/users/password-reset/',
    '/users/verify-otp/',
    '/users/set-new-password/',
    '/users/password-reset-complete/',
    '/logout/',
    '/admin/login/',
    '/secure/',                   # Módulo seguro - tiene sus propias validaciones
]

# Lista de URLs que no deben ser guardadas como destino de redirección
IGNORED_REDIRECT_URLS = [
    '/.well-known/',              # Solicitudes automáticas del navegador
    '/favicon.ico',               # Favicon
    '/robots.txt',                # Robots.txt
    '/sitemap.xml',               # Sitemap
    '/manifest.json',             # Web app manifest
    '/service-worker.js',         # Service worker
    '/.well-known/appspecific/',  # Configuraciones específicas del navegador
]

class TwoFactorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Bypass 2FA globally if enabled via settings (temporary troubleshooting)
        from django.conf import settings
        if getattr(settings, 'TWO_FACTOR_BYPASS', False):
            return self.get_response(request)

        # Si el usuario no está autenticado, continuar normalmente
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        print(f"\n[DEBUG] TwoFactorMiddleware - Usuario autenticado: {request.user.username}")
        print(f"[DEBUG] Path actual: {request.path}")
        
        # Comprobar si la ruta actual está en la lista de exentas
        path = request.path
        if self.is_exempt_path(path):
            print(f"[DEBUG] Ruta {path} está exenta de 2FA")
            return self.get_response(request)
        
        # Verificar si el usuario tiene dispositivos TOTP confirmados
        # Usamos filter().exists() en lugar de verificar la columna usr_2fa
        has_confirmed_devices = TOTPDevice.objects.filter(user=request.user, confirmed=True).exists()
        print(f"[DEBUG] Usuario {request.user.username} tiene dispositivos 2FA confirmados: {has_confirmed_devices}")
        
        # Verificar también el valor de usr_2fa para entender posibles discrepancias
        usr_2fa_value = getattr(request.user, 'usr_2fa', None)
        print(f"[DEBUG] Valor de usr_2fa en la BD: {usr_2fa_value}")
        
        # IMPORTANTE: Si el usuario no tiene dispositivos confirmados, NUNCA debe ir a verificar
        # Debe ir SIEMPRE a setup
        if not has_confirmed_devices:
            print("[DEBUG] Usuario sin dispositivos confirmados")
            # No permitir acceso a la página de verificación si no hay dispositivos confirmados
            if path.startswith('/two_factor/verify/'):
                print(f"[DEBUG] Redirigiendo de verify a setup porque no hay dispositivos confirmados")
                messages.warning(request, "Primero debes configurar la autenticación de dos factores antes de verificar un código.")
                return redirect('two_factor_auth:setup')
            
            # Si no es la página de verificación y no estamos en una URL exenta, redirigir a setup
            if not self.is_exempt_path(path):
                print(f"[DEBUG] Redirigiendo a setup desde {path}")
                
                # Verificar si ya hay un mensaje similar en la cola para evitar duplicados
                existing_messages = [m.message for m in messages.get_messages(request)]
                setup_message = "La autenticación de dos factores es obligatoria. Por favor, configúrala para continuar."
                
                # Solo agregar el mensaje si no existe ya uno similar
                if setup_message not in "".join(str(m) for m in existing_messages):
                    messages.warning(request, setup_message)
                    
                # Guardar la URL actual para redirigir después de la configuración
                self.save_next_url(request)
                return redirect('two_factor_auth:setup')
        
        # Si tiene 2FA pero no ha verificado en esta sesión
        if has_confirmed_devices and not request.session.get('2fa_verified'):
            print(f"[DEBUG] Usuario tiene dispositivos confirmados pero no ha verificado en esta sesión.")
            print(f"[DEBUG] 2fa_verified en sesión: {request.session.get('2fa_verified')}")
            # Evitar redirecciones infinitas verificando que no estemos en páginas de 2FA
            if not path.startswith('/two_factor/'):
                print(f"[DEBUG] Redirigiendo a verify desde {path}")
                
                # Verificar si ya hay un mensaje similar en la cola para evitar duplicados
                existing_messages = [m.message for m in messages.get_messages(request)]
                verify_message = "Por razones de seguridad, debes verificar tu identidad con autenticación de dos factores."
                
                # Solo agregar el mensaje si no existe ya uno similar
                if verify_message not in "".join(str(m) for m in existing_messages):
                    messages.warning(request, verify_message)
                    
                # Guardar la URL actual para redirigir después de la verificación
                self.save_next_url(request)
                return redirect('two_factor_auth:verify')
        
        print("[DEBUG] Continuando con la solicitud normalmente")
        # Continuar con la solicitud normalmente
        return self.get_response(request)
    
    def is_exempt_path(self, path):
        """Verifica si la ruta está exenta de la verificación 2FA"""
        # Comprobar coincidencias exactas y prefijos
        is_exempt = any(
            path == exempt_url or path.startswith(exempt_url)
            for exempt_url in EXEMPT_URLS
        )
        print(f"[DEBUG] is_exempt_path: {path} es exenta: {is_exempt}")
        return is_exempt
    
    def save_next_url(self, request):
        """Guarda la URL actual como próximo destino, evitando URLs de autenticación y solicitudes automáticas"""
        # No guardar URLs de autenticación
        if request.path.startswith('/two_factor/') or request.path.startswith('/users/'):
            return
        
        # No guardar URLs que son solicitudes automáticas del navegador
        for ignored_url in IGNORED_REDIRECT_URLS:
            if request.path.startswith(ignored_url):
                print(f"[DEBUG] Ignorando URL para redirección: {request.path}")
                return
        
        # Solo guardar URLs válidas que no sean solicitudes automáticas
        request.session['next'] = request.path
        print(f"[DEBUG] Guardando next URL en sesión: {request.path}")