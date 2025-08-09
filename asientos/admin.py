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
    list_display = ('id', 'fecha', 'id_perfil')  # Use id_perfil instead of empresa
    list_filter = ('fecha', 'id_perfil')  # Use id_perfil instead of empresa
    search_fields = ('id', 'id_perfil__descripcion')  # Use id_perfil relationship
    readonly_fields = ('id',)
    inlines = [AsientoDetalleInline]
