from django.db import models
from django.conf import settings
import hashlib
from django.core.exceptions import ValidationError
from plan_cuentas.models import PlanCuenta

class Perfil(models.Model):
    id = models.CharField(primary_key=True, max_length=64, editable=False)
    empresa = models.CharField(max_length=24, default="DEFAULT")
    secuencial = models.IntegerField(default=0)
    descripcion = models.CharField(max_length=64, blank=True, null=True)
    vigencia = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        verbose_name = "Perfil Contable"
        verbose_name_plural = "Perfiles Contables"
        ordering = ['secuencial']
        # Define composite unique constraint (not primary key since we now have id)
        unique_together = ('empresa', 'secuencial')

    def save(self, *args, **kwargs):
        # Si el ID ya está establecido, lo respetamos
        # De lo contrario, generamos uno basado en empresa y secuencial
        if not self.id:
            # Create a string combining empresa and secuencial
            unique_str = f"{self.empresa}-{self.secuencial}"
            # Generate a hash from the string
            self.id = hashlib.sha256(unique_str.encode()).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.empresa} - {self.secuencial} - {self.descripcion}"


class PerfilPlanCuenta(models.Model):
    empresa = models.CharField(max_length=24, editable=False, help_text="Se deriva automáticamente del perfil seleccionado.")
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name="cuentas_configuradas", verbose_name="Perfil Contable")
    cuenta = models.ForeignKey(PlanCuenta, on_delete=models.CASCADE, related_name="perfiles_configurados", verbose_name="Cuenta Contable")

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
        unique_together = ('empresa', 'perfil', 'cuenta')
        ordering = ['empresa', 'perfil__secuencial', 'cuenta__codigocuenta']

    def clean(self):
        super().clean()
        if self.perfil_id and self.cuenta_id:
            if self.perfil.empresa != self.cuenta.empresa:
                raise ValidationError(
                    {'cuenta': "La empresa del perfil y la empresa de la cuenta deben ser la misma."}
                )
            # Ensure empresa field is consistent
            if hasattr(self, 'empresa') and self.empresa and self.empresa != self.perfil.empresa:
                 raise ValidationError(
                    {'empresa': f"La empresa ({self.empresa}) no coincide con la empresa del perfil ({self.perfil.empresa}). Este campo se actualiza automáticamente."}
                )

    def save(self, *args, **kwargs):
        if self.perfil_id:
            self.empresa = self.perfil.empresa
        # It's good practice to call full_clean before saving,
        # especially if you have custom validation logic in clean().
        # However, full_clean() is not called automatically on save() by default for performance reasons,
        # but Django admin does call it.
        # For consistency, especially if creating instances outside admin:
        if kwargs.get('force_insert', False) or kwargs.get('force_update', False) or not self.pk:
             # Call clean only for new objects or when forced, to avoid issues with existing valid data
             # if clean logic changes. Or always call it if that's the desired behavior.
            self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        perfil_desc = self.perfil.id if self.perfil_id and self.perfil else "N/A"
        cuenta_desc = self.cuenta.codigocuenta if self.cuenta_id and self.cuenta else "N/A"
        return f"Empresa: {self.empresa} | Perfil: {perfil_desc} | Cuenta: {cuenta_desc} ({self.get_polaridad_display()})"
