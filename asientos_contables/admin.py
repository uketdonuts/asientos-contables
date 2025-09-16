from django.contrib import admin
from django.contrib import messages
from django.urls import path
from django.http import HttpResponseRedirect
from django.shortcuts import render
from .models import SMTPConfiguration


@admin.register(SMTPConfiguration)
class SMTPConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email_host', 'email_port', 'email_host_user', 'is_active', 'created_at')
    list_filter = ('is_active', 'email_use_tls', 'email_use_ssl', 'created_at')
    search_fields = ('name', 'email_host', 'email_host_user', 'default_from_email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información General', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Configuración del Servidor', {
            'fields': ('email_host', 'email_port', 'email_use_tls', 'email_use_ssl')
        }),
        ('Autenticación', {
            'fields': ('email_host_user', 'email_host_password')
        }),
        ('Configuración de Envío', {
            'fields': ('default_from_email', 'test_email')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['test_smtp_connection', 'activate_configuration']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:config_id>/test-email/', 
                 self.admin_site.admin_view(self.test_email_view), 
                 name='smtp_test_email'),
        ]
        return custom_urls + urls
    
    def test_email_view(self, request, config_id):
        """Vista personalizada para enviar email de prueba"""
        try:
            config = SMTPConfiguration.objects.get(id=config_id)
            success, message = config.send_test_email()
            
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
                
        except SMTPConfiguration.DoesNotExist:
            messages.error(request, "Configuración SMTP no encontrada")
        except ValueError as e:
            messages.error(request, str(e))
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))
    
    def test_smtp_connection(self, request, queryset):
        """Acción para probar conexión SMTP"""
        results = []
        
        for config in queryset:
            if not config.test_email:
                results.append(f"{config.name}: Error - Email de prueba no configurado")
                continue
            
            success, message = config.send_test_email()
            status = "Éxito" if success else "Error"
            results.append(f"{config.name}: {status} - {message}")
        
        # Mostrar resultados
        for result in results:
            if "Éxito" in result:
                messages.success(request, result)
            else:
                messages.error(request, result)
    
    test_smtp_connection.short_description = "Enviar email de prueba a configuraciones seleccionadas"
    
    def activate_configuration(self, request, queryset):
        """Acción para activar una configuración SMTP"""
        if queryset.count() > 1:
            messages.error(request, "Solo puede activar una configuración a la vez")
            return
        
        config = queryset.first()
        
        # Desactivar todas las demás
        SMTPConfiguration.objects.update(is_active=False)
        
        # Activar la seleccionada
        config.is_active = True
        config.save()
        
        messages.success(request, f"Configuración '{config.name}' activada exitosamente")
    
    activate_configuration.short_description = "Activar configuración SMTP seleccionada"
    
    def save_model(self, request, obj, form, change):
        """Personalizar guardado para mostrar mensajes"""
        super().save_model(request, obj, form, change)
        
        if obj.is_active:
            messages.success(request, 
                f"Configuración '{obj.name}' guardada y activada. "
                "Los cambios se aplicarán a la configuración de email del sistema.")
        else:
            messages.info(request, f"Configuración '{obj.name}' guardada pero no está activa.")

    def get_readonly_fields(self, request, obj=None):
        """Hacer algunos campos de solo lectura para usuarios no superusuarios"""
        readonly = list(self.readonly_fields)
        
        if not request.user.is_superuser:
            readonly.extend(['email_host_password'])
        
        return readonly

    class Media:
        css = {
            'all': ('admin/css/smtp_config.css',)
        }
        js = ('admin/js/smtp_config.js',)