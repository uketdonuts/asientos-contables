from django.contrib import admin
from .models import AccountingEntry

AccountingEntry._meta.verbose_name = "Asiento contable"
AccountingEntry._meta.verbose_name_plural = "Asientos contables"

admin.site.site_header = "Administración de Asientos Contables"

@admin.register(AccountingEntry)
class AccountingEntryAdmin(admin.ModelAdmin):
    list_display = ('asc_id', 'asc_date', 'asc_amount', 'asc_description', 'asc_currency_type', 'asc_user', 'asc_transaction_id', 'created_at')
    search_fields = ('asc_description', 'asc_user__username')
    list_filter = ('asc_date', 'asc_currency_type')
    ordering = ('-asc_date',)