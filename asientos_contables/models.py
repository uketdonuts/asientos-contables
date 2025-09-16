from django.db import models
from django.core.exceptions import ValidationError


class SMTPConfiguration(models.Model):
    """Configuración SMTP editable desde el admin de Django"""
    
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre de Configuración")
    email_host = models.CharField(max_length=200, verbose_name="Servidor SMTP")
    email_port = models.IntegerField(default=587, verbose_name="Puerto SMTP")
    email_use_tls = models.BooleanField(default=True, verbose_name="Usar TLS")
    email_use_ssl = models.BooleanField(default=False, verbose_name="Usar SSL")
    email_host_user = models.CharField(max_length=200, verbose_name="Usuario SMTP")
    email_host_password = models.CharField(max_length=200, verbose_name="Contraseña SMTP")
    default_from_email = models.EmailField(verbose_name="Email Remitente Por Defecto")
    is_active = models.BooleanField(default=False, verbose_name="Configuración Activa")
    
    # Campos adicionales para testing y configuración
    test_email = models.EmailField(blank=True, null=True, verbose_name="Email para Pruebas")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración SMTP"
        verbose_name_plural = "Configuraciones SMTP"
        ordering = ['-is_active', 'name']

    def clean(self):
        super().clean()
        
        # Validar que solo una configuración pueda estar activa
        if self.is_active:
            active_configs = SMTPConfiguration.objects.filter(is_active=True)
            if self.pk:
                active_configs = active_configs.exclude(pk=self.pk)
            
            if active_configs.exists():
                raise ValidationError("Solo puede haber una configuración SMTP activa a la vez.")
        
        # Validar configuración SSL/TLS
        if self.email_use_ssl and self.email_use_tls:
            raise ValidationError("No se puede usar SSL y TLS al mismo tiempo.")
        
        # Validar puerto común para SSL
        if self.email_use_ssl and self.email_port not in [465, 993, 995]:
            raise ValidationError("Para SSL, se recomienda usar puerto 465, 993 o 995.")
        
        # Validar puerto común para TLS
        if self.email_use_tls and self.email_port not in [587, 25]:
            raise ValidationError("Para TLS, se recomienda usar puerto 587 o 25.")

    def save(self, *args, **kwargs):
        self.clean()
        
        # Si esta configuración se marca como activa, desactivar las demás
        if self.is_active:
            SMTPConfiguration.objects.filter(is_active=True).update(is_active=False)
        
        super().save(*args, **kwargs)
        
        # Aplicar configuración si está activa
        if self.is_active:
            self.apply_to_settings()

    def apply_to_settings(self):
        """Aplica esta configuración a Django settings"""
        from django.conf import settings
        
        settings.EMAIL_HOST = self.email_host
        settings.EMAIL_PORT = self.email_port
        settings.EMAIL_USE_TLS = self.email_use_tls
        settings.EMAIL_USE_SSL = self.email_use_ssl
        settings.EMAIL_HOST_USER = self.email_host_user
        settings.EMAIL_HOST_PASSWORD = self.email_host_password
        settings.DEFAULT_FROM_EMAIL = self.default_from_email
        settings.SERVER_EMAIL = self.default_from_email

    def send_test_email(self):
        """Envía un email de prueba para verificar la configuración"""
        if not self.test_email:
            raise ValueError("Debe especificar un email para pruebas")
        
        from django.core.mail import send_mail
        from django.conf import settings
        
        # Aplicar temporalmente esta configuración
        original_settings = {}
        for setting in ['EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_USE_TLS', 'EMAIL_USE_SSL', 
                       'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD', 'DEFAULT_FROM_EMAIL']:
            original_settings[setting] = getattr(settings, setting, None)
        
        try:
            self.apply_to_settings()
            
            send_mail(
                subject=f'Prueba de configuración SMTP - {self.name}',
                message=f'Este es un email de prueba enviado desde la configuración SMTP "{self.name}".\n\n'
                       f'Servidor: {self.email_host}:{self.email_port}\n'
                       f'TLS: {self.email_use_tls}\n'
                       f'SSL: {self.email_use_ssl}\n'
                       f'Usuario: {self.email_host_user}\n\n'
                       f'Si recibiste este mensaje, la configuración funciona correctamente.',
                from_email=self.default_from_email,
                recipient_list=[self.test_email],
                fail_silently=False,
            )
            return True, "Email de prueba enviado exitosamente"
        
        except Exception as e:
            return False, f"Error enviando email de prueba: {str(e)}"
        
        finally:
            # Restaurar configuraciones originales
            for setting, value in original_settings.items():
                if value is not None:
                    setattr(settings, setting, value)

    def __str__(self):
        active_indicator = " (ACTIVA)" if self.is_active else ""
        return f"{self.name}{active_indicator}"

    @classmethod
    def get_active_config(cls):
        """Obtiene la configuración SMTP activa"""
        return cls.objects.filter(is_active=True).first()

    @classmethod
    def apply_active_config(cls):
        """Aplica la configuración SMTP activa a Django settings"""
        active_config = cls.get_active_config()
        if active_config:
            active_config.apply_to_settings()
            return active_config
        return None