from django import forms
from django.core.exceptions import ValidationError
from .models import AccountingEntry

class AccountingEntryForm(forms.ModelForm):
  
    class Meta:
        model = AccountingEntry
        fields = ['asc_date', 'asc_amount', 'asc_description', 'asc_currency_type']
        widgets = {
            'asc_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'asc_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'asc_description': forms.Textarea(attrs={'class': 'form-control'}),
            'asc_currency_type': forms.Select(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'asc_date': {'required': 'Date is required'},
            'asc_amount': {'required': 'Amount is required'},
            'asc_description': {'required': 'Description is required'},
            'asc_currency_type': {'required': 'Currency type is required'},
        }