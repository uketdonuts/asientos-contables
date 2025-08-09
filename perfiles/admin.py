from django.contrib import admin
from .models import Perfil, PerfilPlanCuenta

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'descripcion')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('id',)

@admin.register(PerfilPlanCuenta)
class PerfilPlanCuentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'perfil_id', 'cuentas_id', 'polaridad')
    list_filter = ('polaridad', 'perfil_id')
    search_fields = ('perfil_id__nombre', 'cuentas_id__cuenta', 'cuentas_id__descripcion')
    autocomplete_fields = ['perfil_id', 'cuentas_id'] # Makes selecting related objects easier

    def get_queryset(self, request):
        # Optimize query to fetch related Perfil and Cuenta objects
        return super().get_queryset(request).select_related('perfil_id', 'cuentas_id')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Potentially filter 'cuentas_id' based on 'perfil_id.plan_cuenta' if needed in admin form
        # This example doesn't implement dynamic filtering in the form itself, 
        # but clean() method in model handles validation.
        # For dynamic filtering in admin, JavaScript or a more complex setup would be needed.
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
