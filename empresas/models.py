from django.db import models
from django.core.exceptions import ValidationError


class Empresa(models.Model):
    """
    Modelo para representar las empresas del sistema contable.
    Cada empresa tiene sus propios asientos, perfiles y plan de cuentas.
    """
    type = models.CharField(
        max_length=50,
        verbose_name="Tipo de Empresa",
        help_text="Tipo o clasificación de la empresa",
        blank=True,
        null=True
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre de la Empresa",
        help_text="Nombre completo de la empresa"
    )
    descripcion = models.TextField(
        verbose_name="Descripción",
        help_text="Descripción adicional de la empresa",
        blank=True,
        null=True
    )
    activa = models.BooleanField(
        default=True,
        verbose_name="¿Empresa Activa?",
        help_text="Indica si la empresa está activa en el sistema"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Modificación"
    )
    
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['nombre']
    
    def clean(self):
        super().clean()
        # Validar que el nombre no esté vacío
        nombre = getattr(self, 'nombre', '')
        if not nombre or not nombre.strip():
            raise ValidationError({
                'nombre': 'El nombre de la empresa es obligatorio.'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.pk or 'Nuevo'} - {self.nombre}"
