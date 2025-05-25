from django.contrib import admin
from .models import PlanCuenta

@admin.register(PlanCuenta)
class PlanCuentaAdmin(admin.ModelAdmin):
    list_display = ('codigocuenta', 'descripcion', 'empresa', 'perfil', 'grupo', 'cuentamadre')
    list_filter = ('empresa', 'perfil', 'grupo')
    search_fields = ('codigocuenta', 'descripcion', 'perfil__descripcion')
    readonly_fields = ()
