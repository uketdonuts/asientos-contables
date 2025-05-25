from django.test import TestCase
from .models import AccountingEntry
from django.contrib.auth import get_user_model

User = get_user_model()

class AccountingEntryModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
            usr_2fa=False,
            usr_fecha_alta='2023-01-01',
            usr_estado='active'
        )
        self.entry = AccountingEntry.objects.create(
            asc_fecha='2023-01-01',
            asc_monto=100.00,
            asc_description='Test Entry',
            asc_tipo_moneda='USD',
            usr_id=self.user,
            id_transaccion='TRANS123',
            fecha_creacion='2023-01-01'
        )

    def test_accounting_entry_creation(self):
        self.assertEqual(self.entry.asc_description, 'Test Entry')
        self.assertEqual(self.entry.asc_monto, 100.00)
        self.assertEqual(self.entry.asc_tipo_moneda, 'USD')
        self.assertEqual(self.entry.usr_id, self.user)

    def test_accounting_entry_str(self):
        self.assertEqual(str(self.entry), f"{self.entry.asc_description} - {self.entry.asc_monto} {self.entry.asc_tipo_moneda}")