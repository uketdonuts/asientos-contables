from django.db import models
from django.conf import settings
import uuid
import hashlib
from perfiles.models import Perfil
from django.core.exceptions import ValidationError

class Asiento(models.Model):
    id = models.CharField(primary_key=True, max_length=64, editable=False)
    empresa = models.CharField(max_length=24, default="DEFAULT")
    fecha = models.DateField(null=False)
    perfil = models.ForeignKey(Perfil, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Perfil Contable")
    # Eliminamos cuenta_debe y cuenta_haber ya que ahora serán parte del detalle
    
    class Meta:
        verbose_name = "Asiento Contable"
        verbose_name_plural = "Asientos Contables"
        ordering = ['-fecha']
        unique_together = ('empresa', 'fecha')

    def save(self, *args, **kwargs):
        if self.perfil:
            self.empresa = self.perfil.empresa
        elif not self.empresa: # If no perfil and empresa is not set (e.g. new instance)
            # Default to "DEFAULT" or raise error if empresa cannot be determined
            # This relies on the model field default="DEFAULT" if not otherwise set.
            # Consider raising ValidationError if empresa is crucial and not determinable.
            pass

        if not self.id:
            if not self.empresa: 
                 raise ValidationError("La empresa es necesaria para generar el ID del asiento y no pudo ser determinada.")
            unique_str = f"{self.empresa}-{self.fecha}"
            self.id = hashlib.sha256(unique_str.encode()).hexdigest()

        # Validate that the sum of details is zero before saving
        # This validation should ideally happen after all details are associated,
        # especially for new asientos where details are added via formset/bulk.
        # The current self.pk condition means it mainly validates existing asientos
        # or if 'detalles' is somehow populated before the first save.
        if self.pk: # Only check if asiento already exists in DB
            total_movimientos = 0
            # Ensure details are loaded if this is an existing instance
            for detalle in self.detalles.all(): # self.detalles requires asiento to have a PK
                if detalle.valor is not None:
                    if detalle.polaridad == '+': # DEBE
                        total_movimientos += detalle.valor
                    elif detalle.polaridad == '-': # HABER
                        total_movimientos -= detalle.valor
            
            if total_movimientos != 0:
                raise ValidationError(f"La suma de los movimientos (debe y haber) debe ser igual a cero para guardar el asiento. Total actual: {total_movimientos}")
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Asiento {self.empresa} - {self.fecha}"
