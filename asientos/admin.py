from django.contrib import admin
from .models import Asiento
from asientos_detalle.models import AsientoDetalle
from asientos_detalle.forms import AsientoDetalleForm, BaseAsientoDetalleInlineFormSet

class AsientoDetalleInline(admin.TabularInline):
    model = AsientoDetalle
    form = AsientoDetalleForm
    formset = BaseAsientoDetalleInlineFormSet
    extra = 1

@admin.register(Asiento)
class AsientoAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'perfil')
    list_filter = ('fecha', 'perfil')
    search_fields = ('id', 'perfil__descripcion')
    readonly_fields = ('id',)
    inlines = [AsientoDetalleInline]
