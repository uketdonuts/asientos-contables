from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)

class SecureSessionMiddleware:
    """
    Middleware para proteger la navegación desde el módulo ultra-seguro
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs que están permitidas cuando hay una sesión segura activa
        self.allowed_secure_urls = [
            '/secure/',           # Módulo seguro completo
            '/logout/',          # Logout estándar del sistema
            '/static/',          # Archivos estáticos
            '/media/',           # Archivos de media
        ]
        
        # URLs que fuerzan logout si se accede desde sesión segura
        self.force_logout_urls = [
            '/asientos/',        # Sistema de asientos
            '/perfiles/',        # Perfiles contables
            '/plan_cuentas/',    # Plan de cuentas
            '/users/perfil/',    # Perfil de usuario
            '/admin/',           # Panel de admin
            '/two_factor/',      # Configuración 2FA
        ]
    
    def __call__(self, request):
        # Solo procesar si el usuario está autenticado
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Verificar si hay una sesión segura activa
        secure_session_active = request.session.get('secure_access_granted', False)
        
        if secure_session_active:
            path = request.path
            
            # Permitir URLs del módulo seguro y archivos estáticos
            if any(path.startswith(allowed) for allowed in self.allowed_secure_urls):
                return self.get_response(request)
            
            # Solo bloquear si el usuario intenta acceder a URLs específicamente prohibidas
            # y ya ha estado trabajando en el módulo seguro por un tiempo
            if any(path.startswith(prohibited) for prohibited in self.force_logout_urls):
                
                # Verificar si ha pasado tiempo suficiente desde que se activó la sesión segura
                secure_access_time = request.session.get('secure_access_time')
                if secure_access_time:
                    import time
                    # Solo aplicar bloqueo si han pasado más de 30 segundos desde el acceso inicial
                    if time.time() - secure_access_time < 30:
                        # Dar mensaje de advertencia pero permitir el acceso
                        messages.info(
                            request,
                            "Tiene una sesión ultra-segura activa. Se recomienda cerrarla antes de navegar a otras secciones."
                        )
                        return self.get_response(request)
                
                # Log del intento de acceso prohibido
                logger.warning(
                    f"Intento de acceso prohibido desde sesión segura: "
                    f"Usuario {request.user.email}, URL: {path}"
                )
                
                # Limpiar sesión segura
                request.session.pop('secure_access_granted', None)
                request.session.pop('secure_password_hash', None)
                request.session.pop('secure_password_type', None)
                request.session.pop('secure_access_time', None)
                request.session.pop('2fa_verified', None)
                
                # Hacer logout completo
                from django.contrib.auth import logout
                logout(request)
                
                messages.warning(
                    request, 
                    "Sesión cerrada automáticamente por acceso prohibido desde módulo ultra-seguro. "
                    "Debe autenticarse nuevamente."
                )
                
                return redirect('users:login')
        
        return self.get_response(request)
