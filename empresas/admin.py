from django.contrib import admin
from .models import Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'type', 'activa', 'fecha_creacion')
    list_filter = ('activa', 'type', 'fecha_creacion')
    search_fields = ('id', 'nombre', 'descripcion')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'nombre', 'type', 'descripcion')
        }),
        ('Estado', {
            'fields': ('activa',)
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
