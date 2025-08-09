from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from secure_data.models import SecureDataMatrix
import json

User = get_user_model()

class MatrixButtonsTest(TestCase):
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

    def test_undo_button(self):
        """Prueba la funcionalidad del botón deshacer"""
        response = self.client.post(
            reverse('secure_data:matrix_undo'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_redo_button(self):
        """Prueba la funcionalidad del botón rehacer"""
        response = self.client.post(
            reverse('secure_data:matrix_redo'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_save_button(self):
        """Prueba la funcionalidad del botón guardar"""
        data = {
            'changes': [
                {
                    'row': 0,
                    'col': 0,
                    'value': 'New Test Value'
                }
            ]
        }
        response = self.client.post(
            reverse('secure_data:matrix_save'),
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        saved_data = SecureDataMatrix.objects.get(
            row_index=0,
            col_index=0,
            user=self.user
        )
        self.assertEqual(saved_data.value, 'New Test Value')

    def test_exit_button(self):
        """Prueba la funcionalidad del botón salir"""
        response = self.client.get(reverse('secure_data:matrix_exit'))
        self.assertEqual(response.status_code, 302)  # Redirección
        self.assertRedirects(response, reverse('home')) 

class MatrixIntegrationTest(TestCase):
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

    def test_matrix_view_load(self):
        """Prueba que la vista de la matriz carga correctamente"""
        response = self.client.get(reverse('secure_data:matrix_view'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'secure_data/matrix_infinite.html')
        
        # Verificar que los datos iniciales están presentes
        self.assertContains(response, 'initialData')
        self.assertContains(response, 'Valor Original')

    def test_matrix_save_load_cycle(self):
        """Prueba un ciclo completo de guardar y cargar datos"""
        # 1. Guardar nuevos datos
        matrix_data = {
            'matrix_data': {
                '0': {
                    '0': 'Nuevo Valor',
                    '1': 'Otro Valor'
                },
                '1': {
                    '0': 'Valor en fila 2'
                }
            }
        }
        
        response = self.client.post(
            reverse('secure_data:save_matrix'),
            data=json.dumps(matrix_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['cells_updated'], 3)
        
        # 2. Verificar que los datos se guardaron
        cells = SecureDataMatrix.objects.filter(user=self.user).order_by('row_index', 'col_index')
        self.assertEqual(cells.count(), 3)
        
        values = [(cell.row_index, cell.col_index, cell.value) for cell in cells]
        expected = [
            (0, 0, 'Nuevo Valor'),
            (0, 1, 'Otro Valor'),
            (1, 0, 'Valor en fila 2')
        ]
        self.assertEqual(values, expected)
        
        # 3. Cargar la vista de nuevo
        response = self.client.get(reverse('secure_data:matrix_view'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar que los nuevos datos están presentes
        self.assertContains(response, 'Nuevo Valor')
        self.assertContains(response, 'Otro Valor')
        self.assertContains(response, 'Valor en fila 2')

    def test_undo_redo_cycle(self):
        """Prueba un ciclo completo de deshacer/rehacer"""
        # 1. Hacer un cambio inicial
        matrix_data = {
            'matrix_data': {
                '0': {
                    '0': 'Valor 1'
                }
            }
        }
        response = self.client.post(
            reverse('secure_data:save_matrix'),
            data=json.dumps(matrix_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # 2. Hacer otro cambio
        matrix_data['matrix_data']['0']['0'] = 'Valor 2'
        response = self.client.post(
            reverse('secure_data:save_matrix'),
            data=json.dumps(matrix_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # 3. Deshacer el último cambio
        response = self.client.post(reverse('secure_data:matrix_undo'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verificar que volvimos al valor anterior
        cell = SecureDataMatrix.objects.get(
            row_index=0,
            col_index=0,
            user=self.user
        )
        self.assertEqual(cell.value, 'Valor 1')
        
        # 4. Rehacer el cambio
        response = self.client.post(reverse('secure_data:matrix_redo'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verificar que volvimos al último valor
        cell.refresh_from_db()
        self.assertEqual(cell.value, 'Valor 2')

    def test_security_checks(self):
        """Prueba las verificaciones de seguridad"""
        # 1. Intentar acceder sin sesión segura
        session = self.client.session
        del session['secure_access_granted']
        session.save()
        
        response = self.client.get(reverse('secure_data:matrix_view'))
        self.assertEqual(response.status_code, 302)  # Redirección
        
        # 2. Intentar guardar sin sesión segura
        matrix_data = {
            'matrix_data': {
                '0': {
                    '0': 'Valor Malicioso'
                }
            }
        }
        response = self.client.post(
            reverse('secure_data:save_matrix'),
            data=json.dumps(matrix_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Acceso no autorizado')
        
        # Verificar que no se guardó nada
        cell = SecureDataMatrix.objects.get(
            row_index=0,
            col_index=0,
            user=self.user
        )
        self.assertEqual(cell.value, 'Valor Original')

    def test_concurrent_edits(self):
        """Prueba ediciones concurrentes"""
        # Crear otro usuario
        other_user = User.objects.create_user(
            email='otro@figbiz.net',
            password='OtroPass123!',
            usr_2fa=False
        )
        other_client = Client()
        other_client.force_login(other_user)
        
        # Configurar sesión segura para el otro usuario
        session = other_client.session
        session['secure_access_granted'] = True
        session['secure_password_hash'] = 'otro_hash'
        session['secure_password_type'] = 'test'
        session.save()
        
        # Crear datos para el otro usuario
        SecureDataMatrix.objects.create(
            row_index=0,
            col_index=0,
            value='Valor del Otro Usuario',
            user=other_user,
            password_hash='otro_hash'
        )
        
        # 1. Usuario 1 guarda un cambio
        matrix_data = {
            'matrix_data': {
                '0': {
                    '0': 'Valor Usuario 1'
                }
            }
        }
        response = self.client.post(
            reverse('secure_data:save_matrix'),
            data=json.dumps(matrix_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # 2. Usuario 2 guarda un cambio en la misma celda
        matrix_data = {
            'matrix_data': {
                '0': {
                    '0': 'Valor Usuario 2'
                }
            }
        }
        response = other_client.post(
            reverse('secure_data:save_matrix'),
            data=json.dumps(matrix_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verificar que cada usuario ve su propio valor
        cell1 = SecureDataMatrix.objects.get(
            row_index=0,
            col_index=0,
            user=self.user
        )
        cell2 = SecureDataMatrix.objects.get(
            row_index=0,
            col_index=0,
            user=other_user
        )
        
        self.assertEqual(cell1.value, 'Valor Usuario 1')
        self.assertEqual(cell2.value, 'Valor Usuario 2') 