from django.contrib import admin
from .models import AsientoDetalle

@admin.register(AsientoDetalle)
class AsientoDetalleAdmin(admin.ModelAdmin):
    list_display = ('id', 'asiento', 'cuenta', 'DetalleDeCausa', 'valor', 'polaridad')
    list_filter = ('polaridad',)
    search_fields = ('DetalleDeCausa', 'Referencia')
    readonly_fields = ()
