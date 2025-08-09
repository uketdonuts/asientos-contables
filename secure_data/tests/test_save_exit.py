from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from secure_data.models import SecureDataMatrix
import json

User = get_user_model()

class SaveExitTest(TestCase):
    def setUp(self):
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            email='c.rodriguez@figbiz.net',
            password='TestPass123!',
            usr_2fa=False  # Desactivamos 2FA para las pruebas
        )
        self.client = Client()
        self.client.force_login(self.user)
        
        # Crear datos de prueba en la matriz
        self.matrix_data = SecureDataMatrix.objects.create(
            row_index=0,
            col_index=0,
            value='Test Value',
            user=self.user
        )

    def test_save_action(self):
        """Prueba la funcionalidad de guardar"""
        data = {
            'changes': [
                {
                    'row': 0,
                    'col': 0,
                    'value': 'New Value'
                }
            ]
        }
        response = self.client.post(
            reverse('secure_data:matrix_save'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verificar que el valor se guardó
        saved_value = SecureDataMatrix.objects.get(
            row_index=0,
            col_index=0,
            user=self.user
        )
        self.assertEqual(saved_value.value, 'New Value')

    def test_exit_action(self):
        """Prueba la funcionalidad de salir"""
        response = self.client.get(reverse('secure_data:matrix_exit'))
        self.assertEqual(response.status_code, 302)  # Redirección 