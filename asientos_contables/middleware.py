from django.utils.deprecation import MiddlewareMixin


class SMTPConfigurationMiddleware(MiddlewareMixin):
    """
    Middleware para aplicar automáticamente la configuración SMTP activa
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Aplicar configuración al inicializar
        self.apply_smtp_config()
        super().__init__(get_response)
    
    def apply_smtp_config(self):
        """Aplica la configuración SMTP activa"""
        try:
            from .models import SMTPConfiguration
            SMTPConfiguration.apply_active_config()
        except Exception:
            # Ignorar errores durante migraciones o cuando no existe la tabla
            pass
    
    def process_request(self, request):
        """Aplicar configuración SMTP en cada request si es necesario"""
        # Solo aplicar en requests admin o cuando sea necesario
        if request.path.startswith('/admin/'):
            self.apply_smtp_config()
        return None