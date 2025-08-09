from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from secure_data.models import SecureDataMatrix
from django.http import HttpResponse
import json
from typing import cast

User = get_user_model()

class UndoRedoTest(TestCase):
    def setUp(self):
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            email='c.rodriguez@figbiz.net',
            password='TestPass123!',
            usr_2fa=False  # Desactivamos 2FA para las pruebas
        )
        self.client = Client()
        self.client.force_login(self.user)
        
        # Configurar sesión segura
        session = self.client.session
        session['secure_access_granted'] = True
        session['secure_password_hash'] = 'test_hash'
        session['secure_password_type'] = 'test'
        session.save()
        
        # Crear datos de prueba en la matriz
        self.matrix_data = SecureDataMatrix.objects.create(
            row_index=0,
            col_index=0,
            value='Valor Original',
            user=self.user,
            password_hash='test_hash'
        )

    def test_undo_redo_sequence(self):
        """Prueba una secuencia completa de acciones deshacer/rehacer"""
        # 1. Hacer un cambio inicial
        change_data = {
            'changes': [{
                'row': 0,
                'col': 0,
                'value': 'Valor Modificado'
            }]
        }
        response = cast(HttpResponse, self.client.post(
            reverse('secure_data:matrix_save'),
            data=json.dumps(change_data),
            content_type='application/json'
        ))
        self.assertEqual(response.status_code, 200)
        
        # 2. Verificar el cambio
        cell = SecureDataMatrix.objects.get(
            row_index=0,
            col_index=0,
            user=self.user
        )
        self.assertEqual(cell.value, 'Valor Modificado')
        
        # 3. Deshacer el cambio
        response = cast(HttpResponse, self.client.post(
            reverse('secure_data:matrix_undo'),
            content_type='application/json'
        ))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(data['success'])
        
        # 4. Verificar que se deshizo el cambio
        cell.refresh_from_db()
        self.assertEqual(cell.value, 'Valor Original')
        
        # 5. Rehacer el cambio
        response = cast(HttpResponse, self.client.post(
            reverse('secure_data:matrix_redo'),
            content_type='application/json'
        ))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode())
        self.assertTrue(data['success'])
        
        # 6. Verificar que se rehizo el cambio
        cell.refresh_from_db()
        self.assertEqual(cell.value, 'Valor Modificado')

    def test_undo_limit(self):
        """Prueba el límite de acciones deshacer"""
        # Realizar múltiples cambios
        values = ['Valor 1', 'Valor 2', 'Valor 3']
        for value in values:
            change_data = {
                'changes': [{
                    'row': 0,
                    'col': 0,
                    'value': value
                }]
            }
            self.client.post(
                reverse('secure_data:matrix_save'),
                data=json.dumps(change_data),
                content_type='application/json'
            )
        
        # Intentar deshacer más allá del límite
        for _ in range(len(values) + 1):
            response = cast(HttpResponse, self.client.post(
                reverse('secure_data:matrix_undo'),
                content_type='application/json'
            ))
            data = json.loads(response.content.decode())
            if _ < len(values):
                self.assertTrue(data['success'])
            else:
                self.assertFalse(data['success'])
                self.assertIn('No hay más acciones para deshacer', data.get('error', ''))

    def test_redo_after_new_change(self):
        """Prueba que rehacer se limpia después de un nuevo cambio"""
        # 1. Hacer cambio inicial
        change_data = {
            'changes': [{
                'row': 0,
                'col': 0,
                'value': 'Valor 1'
            }]
        }
        self.client.post(
            reverse('secure_data:matrix_save'),
            data=json.dumps(change_data),
            content_type='application/json'
        )
        
        # 2. Deshacer el cambio
        self.client.post(
            reverse('secure_data:matrix_undo'),
            content_type='application/json'
        )
        
        # 3. Hacer un nuevo cambio
        change_data['changes'][0]['value'] = 'Valor Nuevo'
        self.client.post(
            reverse('secure_data:matrix_save'),
            data=json.dumps(change_data),
            content_type='application/json'
        )
        
        # 4. Intentar rehacer (debería fallar)
        response = cast(HttpResponse, self.client.post(
            reverse('secure_data:matrix_redo'),
            content_type='application/json'
        ))
        data = json.loads(response.content.decode())
        self.assertFalse(data['success'])
        self.assertIn('No hay acciones para rehacer', data.get('error', '')) 