from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import hashlib

class Perfil(models.Model):
    id = models.CharField(primary_key=True, max_length=64, editable=False)
    nombre = models.CharField(max_length=64, verbose_name="Nombre del Perfil")
    descripcion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Perfil Contable"
        verbose_name_plural = "Perfiles Contables"
        ordering = ['nombre']

    def save(self, *args, **kwargs):
        # Si el ID no está establecido, generar uno basado en el nombre
        if not self.id:
            unique_str = f"{self.nombre}-{hash(self.nombre)}"
            self.id = hashlib.sha256(unique_str.encode()).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre}"


class PerfilPlanCuenta(models.Model):
    id = models.AutoField(primary_key=True)  # Campo ID explícito según diagrama
    empresa = models.CharField(max_length=24, default='DEFAULT', verbose_name="Empresa")
    cuentas_id = models.ForeignKey('plan_cuentas.Cuenta', on_delete=models.CASCADE, related_name="perfiles_configurados", verbose_name="Cuenta Contable", db_column="cuenta_id")  # Restored to not nullable
    perfil_id = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name="cuentas_configuradas", verbose_name="Perfil Contable", db_column="perfil_id")

    POLARIDAD_CHOICES = [
        ('+', 'Positiva (+ / Debe)'),
        ('-', 'Negativa (- / Haber)'),
    ]
    polaridad = models.CharField(
        max_length=1,
        choices=POLARIDAD_CHOICES,
        verbose_name="Polaridad",
        help_text="Define la naturaleza de la cuenta dentro del perfil (ej. '+' para Debe, '-' para Haber)."
    )

    class Meta:
        verbose_name = "Configuración de Cuenta en Perfil"
        verbose_name_plural = "Configuraciones de Cuentas en Perfiles"
        unique_together = ('perfil_id', 'cuentas_id')
        ordering = ['perfil_id__nombre', 'cuentas_id__descripcion']

    def clean(self):
        super().clean()
        # Validar que el perfil y la cuenta pertenezcan a la misma empresa
        if self.perfil_id and self.cuentas_id:
            if hasattr(self.cuentas_id, 'plan_cuentas'):
                # Comparar los IDs de empresa a través del plan de cuentas
                cuenta_empresa = self.cuentas_id.plan_cuentas.empresa.pk if self.cuentas_id.plan_cuentas and self.cuentas_id.plan_cuentas.empresa else None
                
                if self.empresa != str(cuenta_empresa):
                    raise ValidationError(
                        {'cuentas_id': f"El perfil ({self.empresa}) y la cuenta ({cuenta_empresa}) deben pertenecer a la misma empresa."}
                    )

    def save(self, *args, **kwargs):
        # Validar antes de guardar
        if kwargs.get('force_insert', False) or kwargs.get('force_update', False) or not self.pk:
            self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        perfil_desc = self.perfil_id.nombre if self.perfil_id and self.perfil_id.nombre else "N/A"
        cuenta_desc = self.cuentas_id.descripcion if self.cuentas_id and self.cuentas_id.descripcion else "N/A"
        return f"Perfil: {perfil_desc} | Cuenta: {cuenta_desc} ({self.get_polaridad_display()})"
