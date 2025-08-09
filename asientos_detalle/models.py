from django.db import models
from asientos.models import Asiento
from plan_cuentas.models import Cuenta
from empresas.models import Empresa

class AsientoDetalle(models.Model):
    TIPO_CUENTA_CHOICES = [
        ('DEBE', 'Cuenta Debe'),
        ('HABER', 'Cuenta Haber'),
    ]
    
    id = models.AutoField(primary_key=True)  # Campo ID explícito según diagrama
    # Commented out ac_head_id field temporarily due to schema issues
    # ac_head_id = models.ForeignKey(  # AC_HEAD_ID según diagrama
    #     Asiento, 
    #     on_delete=models.CASCADE,
    #     related_name='detalles',
    #     db_column="ac_head_id",
    #     verbose_name="Asiento Contable",
    #     null=True,  # Temporalmente nullable para la migración
    #     blank=True
    # )
    
    # Use the existing asiento field instead if it exists
    asiento = models.ForeignKey(
        Asiento,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Asiento Contable"
    )
    cuenta = models.ForeignKey(  # Relación con CUENTAS según diagrama
        Cuenta, 
        on_delete=models.CASCADE,
        related_name='asientos_detalles',
        verbose_name="Cuenta Contable"
    )
    empresa_id = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        verbose_name="Empresa",
        null=True,
        blank=True
    )
    polaridad = models.CharField(max_length=1, choices=[('+', 'Positivo'), ('-', 'Negativo')], verbose_name="Polaridad", default='-')
    valor = models.FloatField(null=True, blank=True, verbose_name="Valor", db_column="valor")  # Use existing column name
    DetalleDeCausa = models.CharField(max_length=64, null=True, blank=True, verbose_name="Detalle de Causa", db_column="DetalleDeCausa")  # Use existing column name
    Referencia = models.CharField(max_length=45, null=True, blank=True, verbose_name="Referencia", db_column="Referencia")  # Use existing column name
    
    # Campo mantenido para compatibilidad
    tipo_cuenta = models.CharField(
        max_length=5, 
        choices=TIPO_CUENTA_CHOICES,
        verbose_name="Tipo de Cuenta",
        default='DEBE'
    )

    class Meta:
        verbose_name = "Detalle de Asiento"
        verbose_name_plural = "Detalles de Asientos"
        ordering = ['asiento', 'id']

    # Properties for backward compatibility
    @property
    def monto(self):
        """Backward compatibility property for valor field"""
        return self.valor
    
    @monto.setter
    def monto(self, value):
        """Backward compatibility setter for valor field"""
        self.valor = value
    
    @property
    def causa(self):
        """Backward compatibility property for DetalleDeCausa field"""
        return self.DetalleDeCausa
    
    @causa.setter
    def causa(self, value):
        """Backward compatibility setter for DetalleDeCausa field"""
        self.DetalleDeCausa = value
    
    @property
    def ref_extra(self):
        """Backward compatibility property for Referencia field"""
        return self.Referencia
    
    @ref_extra.setter
    def ref_extra(self, value):
        """Backward compatibility setter for Referencia field"""
        self.Referencia = value

    def __str__(self):
        return f"Detalle {self.tipo_cuenta} para Asiento {self.asiento.id} - {self.cuenta}"
    
    def save(self, *args, **kwargs):
        # Lógica de validación y guardado
        super().save(*args, **kwargs)
