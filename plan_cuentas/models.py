from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class PlanCuenta(models.Model):
    """
    Plan de Cuentas - Catálogo de planes contables por empresa
    Contiene ID, empresa y descripción como referencia general
    """
    id = models.AutoField(primary_key=True)
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.CASCADE,
        verbose_name="Empresa",
        help_text="Empresa a la que pertenece el plan de cuentas"
    )
    descripcion = models.CharField(
        max_length=255, 
        verbose_name="Descripción del Plan de Cuentas"
    )
    perfil = models.ForeignKey(
        'perfiles.Perfil',
        on_delete=models.CASCADE,
        verbose_name="Perfil",
        db_column="perfil_id",
        help_text="Perfil contable asociado"
    )

    class Meta:
        verbose_name = "Plan de Cuentas"
        verbose_name_plural = "Planes de Cuentas"
        ordering = ['empresa', 'descripcion']
        unique_together = ('empresa', 'descripcion')  # Plan único por empresa

    def clean(self):
        super().clean()
        if not self.empresa:
            raise ValidationError({'empresa': 'La empresa es obligatoria.'})
        if not self.perfil:
            raise ValidationError({'perfil': 'El perfil es obligatorio.'})
        if not self.descripcion:
            raise ValidationError({'descripcion': 'La descripción es obligatoria.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        try:
            empresa_nombre = self.empresa.nombre
        except AttributeError:
            empresa_nombre = "Sin empresa"
        return f"{self.descripcion} - {empresa_nombre}"


class Cuenta(models.Model):
    """
    Cuentas contables - Cuentas individuales dentro de un plan de cuentas
    """
    id = models.AutoField(primary_key=True)
    cuenta = models.CharField(
        max_length=14, 
        verbose_name="Código de Cuenta"
    )
    descripcion = models.CharField(
        max_length=255, 
        verbose_name="Descripción de la Cuenta"
    )
    cuenta_madre = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Cuenta Madre",
        help_text="Cuenta padre en la jerarquía",
        related_name="cuentas_hijas"
    )
    plan_cuentas = models.ForeignKey(
        PlanCuenta,
        on_delete=models.CASCADE,
        verbose_name="Plan de Cuentas",
        help_text="Plan de cuentas al que pertenece"
    )
    grupo = models.IntegerField(
        verbose_name="Grupo", 
        help_text="1=Activos, 2=Pasivos, 3=Patrimonio, 4=Ingresos, 5=Gastos",
        null=True,
        blank=True
    )
    perfil = models.ForeignKey(
        'perfiles.Perfil',
        on_delete=models.CASCADE,
        verbose_name="Perfil",
        db_column="perfil_id",
        help_text="Perfil contable asociado",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Cuenta Contable"
        verbose_name_plural = "Cuentas Contables"
        ordering = ['plan_cuentas', 'cuenta']
        unique_together = ('plan_cuentas', 'cuenta')  # Código único por plan de cuentas

    def clean(self):
        super().clean()
        if not self.cuenta:
            raise ValidationError({'cuenta': 'El código de cuenta es obligatorio.'})
        if not self.descripcion:
            raise ValidationError({'descripcion': 'La descripción es obligatoria.'})
        if not self.plan_cuentas:
            raise ValidationError({'plan_cuentas': 'El plan de cuentas es obligatorio.'})
        # Validar que la cuenta madre pertenezca al mismo plan de cuentas
        if self.cuenta_madre and self.cuenta_madre.plan_cuentas != self.plan_cuentas:
            raise ValidationError({
                'cuenta_madre': 'La cuenta madre debe pertenecer al mismo plan de cuentas.'
            })

    def save(self, *args, **kwargs):
        # Si no se especifica perfil para la cuenta, heredar del plan
        if not self.perfil and self.plan_cuentas and getattr(self.plan_cuentas, 'perfil_id', None):
            self.perfil_id = self.plan_cuentas.perfil_id
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cuenta} - {self.descripcion}"
