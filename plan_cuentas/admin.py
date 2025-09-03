from django.contrib import admin
from .models import PlanCuenta, Cuenta

@admin.register(PlanCuenta)
class PlanCuentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'empresa', 'descripcion', 'perfil')
    list_filter = ('empresa', 'perfil')
    search_fields = ('descripcion', 'empresa__nombre')
    readonly_fields = ()
    ordering = ('empresa', 'descripcion')

@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cuenta', 'descripcion', 'plan_cuentas', 'perfil', 'cuenta_madre', 'grupo')
    list_filter = ('plan_cuentas', 'perfil', 'grupo')
    search_fields = ('cuenta', 'descripcion', 'plan_cuentas__descripcion')
    readonly_fields = ('id',)
    ordering = ('plan_cuentas', 'cuenta')
