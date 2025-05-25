from django.db import models
from django.conf import settings

class AccountingEntry(models.Model):
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
    ]

    asc_id = models.AutoField(primary_key=True)
    asc_date = models.DateField()
    asc_amount = models.DecimalField(max_digits=10, decimal_places=2)
    asc_description = models.TextField()
    asc_currency_type = models.CharField(max_length=3, choices=CURRENCY_CHOICES)  # e.g., USD, EUR
    asc_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    asc_transaction_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Asiento Contable"
        verbose_name_plural = "Asientos Contables"

    def __str__(self):
        return f"{self.asc_description} - {self.asc_amount} {self.asc_currency_type}"