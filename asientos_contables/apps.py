from django.apps import AppConfig


class AsientosContablesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'asientos_contables'
    verbose_name = 'Configuraciones del Sistema'
    
    def ready(self):
        """Configuraciones que se ejecutan cuando la app está lista"""
        # Aplicar configuración SMTP activa al iniciar
        try:
            from .models import SMTPConfiguration
            SMTPConfiguration.apply_active_config()
        except Exception:
            # Ignorar errores durante migraciones o cuando no existe la tabla
            pass