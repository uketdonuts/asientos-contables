from django.contrib import admin
from .models import SecureDataMatrix, SecureAccessLog, SecurePassword

@admin.register(SecureDataMatrix)
class SecureDataMatrixAdmin(admin.ModelAdmin):
    list_display = ('id', 'data_type', 'row_index', 'col_index', 'created_at')
    list_filter = ('data_type', 'created_at')
    search_fields = ('id',)
    readonly_fields = ('id', 'encrypted_value', 'encryption_salt', 'created_at', 'updated_at')
    
    def has_view_permission(self, request, obj=None):
        # Solo superusers pueden ver estos datos
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return False  # No permitir edición desde admin
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(SecureAccessLog)
class SecureAccessLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'access_time', 'ip_address', 'password_type', 'success')
    list_filter = ('password_type', 'success', 'access_time')
    search_fields = ('user__email', 'ip_address')
    readonly_fields = ('user', 'access_time', 'ip_address', 'password_type', 'success', 'user_agent')
    
    def has_add_permission(self, request):
        return False  # Los logs se crean automáticamente
    
    def has_change_permission(self, request, obj=None):
        return False  # Los logs son inmutables

@admin.register(SecurePassword)
class SecurePasswordAdmin(admin.ModelAdmin):
    list_display = ('password_text', 'password_type', 'is_active', 'description', 'created_at')
    list_filter = ('password_type', 'is_active', 'created_at')
    search_fields = ('password_text', 'description')
    readonly_fields = ('id', 'password_hash', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('password_text', 'password_type', 'description', 'is_active')
        }),
        ('Información Técnica', {
            'fields': ('id', 'password_hash'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_view_permission(self, request, obj=None):
        # Solo superusers pueden ver las contraseñas
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        # Solo superusers pueden modificar
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        # Solo superusers pueden eliminar
        return request.user.is_superuser
