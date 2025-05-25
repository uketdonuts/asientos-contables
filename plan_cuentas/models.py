from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class PlanCuenta(models.Model):
    empresa = models.CharField(max_length=24, default="DEFAULT")
    perfil = models.ForeignKey(
        'perfiles.Perfil',  # Use string reference
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Perfil Contable Asociado",
        related_name="cuentas_directas"
    )
    grupo = models.IntegerField(default=0)
    codigocuenta = models.CharField(max_length=14, default="DEFAULT")
    descripcion = models.CharField(max_length=80, blank=True, null=True)
    cuentamadre = models.CharField(max_length=14, blank=True, null=True)

    class Meta:
        verbose_name = "Cuenta Contable"
        verbose_name_plural = "Plan de Cuentas"
        ordering = ['codigocuenta']
        unique_together = ('empresa', 'codigocuenta') # Asumiendo que codigocuenta es único por empresa

    def clean(self):
        super().clean()
        if self.perfil:
            if self.empresa != self.perfil.empresa:
                raise ValidationError({
                    'perfil': f"La empresa de la cuenta ('{self.empresa}') no coincide con la empresa del perfil seleccionado ('{self.perfil.empresa}').",
                    'empresa': f"La empresa de la cuenta ('{self.empresa}') no coincide con la empresa del perfil seleccionado ('{self.perfil.empresa}')."
                })

    def save(self, *args, **kwargs):
        if self.perfil and not self.empresa:
             self.empresa = self.perfil.empresa
        elif self.perfil and self.empresa and self.empresa != self.perfil.empresa:
            raise ValidationError(f"Conflicto de empresas: Cuenta '{self.empresa}', Perfil '{self.perfil.empresa}'.")
        
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.perfil:
            return f"{self.codigocuenta} - {self.descripcion} (Perfil: {self.perfil.secuencial})"
        return f"{self.codigocuenta} - {self.descripcion}"
