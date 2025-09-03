from django.db import models
from django.conf import settings
import uuid
import hashlib
from django.core.exceptions import ValidationError
from django.utils import timezone

class Asiento(models.Model):
    id = models.CharField(primary_key=True, max_length=64, editable=False)
    fecha = models.DateField(null=False, verbose_name="Fecha")
    empresa = models.CharField(max_length=24, default='DEFAULT', verbose_name="Empresa")
    id_perfil = models.ForeignKey(  # Campo ID_PERFIL según diagrama
        'perfiles.Perfil',
        on_delete=models.CASCADE,
        verbose_name="Perfil",
        help_text="Perfil contable asociado al asiento",
        db_column="id_perfil",
        null=True,  # Temporalmente nullable para permitir datos existentes
        blank=True
    )
    
    # Campos de auditoría y descripción
    descripcion = models.TextField(
        max_length=500, 
        blank=True, 
        null=True,
        verbose_name="Descripción",
        help_text="Descripción del asiento contable"
    )
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,  # No permitir eliminar usuario si tiene asientos
        related_name='asientos_creados',
        verbose_name="Usuario Creador",
        help_text="Usuario que creó el asiento",
        null=True,
        blank=True
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación",
        help_text="Fecha y hora cuando se creó el asiento"
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='asientos_modificados',
        verbose_name="Usuario Modificación",
        help_text="Último usuario que modificó el asiento",
        null=True,
        blank=True
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Modificación",
        help_text="Fecha y hora de la última modificación"
    )
    
    class Meta:
        verbose_name = "Asiento Contable"
        verbose_name_plural = "Asientos Contables"
        ordering = ['-fecha']

    @property
    def empresa_obj(self):
        """
        Obtiene la empresa del asiento
        """
        return self.empresa

    def save(self, *args, **kwargs):
        if not self.id:
            # Generar ID basado en fecha y timestamp para evitar colisiones
            import time
            timestamp = str(int(time.time()))
            unique_str = f"{self.fecha}-{timestamp}"
            self.id = hashlib.sha256(unique_str.encode()).hexdigest()

        # Validate that the sum of details is zero before saving
        if self.pk: # Only check if asiento already exists in DB
            total_movimientos = 0
            # Ensure details are loaded if this is an existing instance
            for detalle in self.detalles.all():
                if detalle.monto is not None:
                    if detalle.polaridad == '+': # DEBE
                        total_movimientos += detalle.monto
                    elif detalle.polaridad == '-': # HABER
                        total_movimientos -= detalle.monto
            
            if total_movimientos != 0:
                raise ValidationError(f"La suma de los movimientos (debe y haber) debe ser igual a cero para guardar el asiento. Total actual: {total_movimientos}")
        
        super().save(*args, **kwargs)

    def __str__(self):
        empresa_desc = self.empresa if self.empresa else "Sin Empresa"
        usuario_info = f" - {self.usuario_creacion.username}" if self.usuario_creacion else ""
        return f"Asiento {empresa_desc} - {self.fecha}{usuario_info}"
