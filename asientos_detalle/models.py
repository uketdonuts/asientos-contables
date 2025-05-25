from django.db import models
from asientos.models import Asiento
from plan_cuentas.models import PlanCuenta

class AsientoDetalle(models.Model):
    TIPO_CUENTA_CHOICES = [
        ('DEBE', 'Cuenta Debe'),
        ('HABER', 'Cuenta Haber'),
    ]
    
    asiento = models.ForeignKey(
        Asiento, 
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    tipo_cuenta = models.CharField(
        max_length=5, 
        choices=TIPO_CUENTA_CHOICES,
        verbose_name="Tipo de Cuenta",
        default='DEBE'  # Valor por defecto
    )
    cuenta = models.ForeignKey(
        PlanCuenta, 
        on_delete=models.CASCADE,
        related_name='asientos_detalles',
        verbose_name="Cuenta Contable",
        null=True  # Permitir nulo temporalmente para la migración
    )
    DetalleDeCausa = models.CharField(max_length=64, null=True, blank=True, verbose_name="Causa")
    Referencia = models.CharField(max_length=45, null=True, blank=True, verbose_name="Referencia Extra")
    valor = models.FloatField(null=True, blank=True, verbose_name="Monto")
    polaridad = models.CharField(max_length=1, null=True, blank=True, choices=[('+', 'Positivo'), ('-', 'Negativo')], verbose_name="Suma/Resta")

    class Meta:
        verbose_name = "Detalle de Asiento"
        verbose_name_plural = "Detalles de Asientos"
        ordering = ['asiento', 'id']  # Changed ordering to use id for consistent order

    def __str__(self):
        return f"Detalle {self.tipo_cuenta} para Asiento {self.asiento.empresa} - {self.asiento.fecha} - {self.cuenta}"
    
    def save(self, *args, **kwargs):
        # Polaridad will now be set based on PerfilPlanCuenta configuration
        # when the AsientoDetalle is created/updated in the views or forms.
        # No longer automatically set based on tipo_cuenta here.
        # if self.tipo_cuenta == 'DEBE':
        #     self.polaridad = '-'
        # elif self.tipo_cuenta == 'HABER':
        #     self.polaridad = '+'
        
        super().save(*args, **kwargs)
