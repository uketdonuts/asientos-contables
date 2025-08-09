from django.contrib import admin
from .models import AsientoDetalle

@admin.register(AsientoDetalle)
class AsientoDetalleAdmin(admin.ModelAdmin):
    list_display = ('id', 'asiento', 'cuenta', 'DetalleDeCausa', 'valor', 'polaridad')  # Use actual database field names
    list_filter = ('polaridad', 'tipo_cuenta')
    search_fields = ('DetalleDeCausa', 'Referencia')  # Use actual database field names
    readonly_fields = ()
