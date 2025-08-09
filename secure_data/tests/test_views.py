from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from secure_data.models import SecureDataMatrix, SecurePassword
import json

User = get_user_model()

class SecureMatrixViewTests(TestCase):
    def setUp(self):
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='c.rodriguez',
            email='c.rodriguez@figbiz.net',
            password='TestPass123!',
            usr_2fa=True
        )
        self.client = Client()
        
        # Crear contraseñas secretas de prueba
        self.decoy_password = SecurePassword.objects.create(
            password_text='TestDecoy123!',
            password_type='decoy',
            description='Test Decoy Password'
        )
        self.real_password = SecurePassword.objects.create(
            password_text='TestReal456!',
            password_type='real',
            description='Test Real Password'
        )
        
        # Iniciar sesión
        self.client.login(username='c.rodriguez', password='TestPass123!')
        
        # Simular acceso seguro concedido
        session = self.client.session
        session['secure_access_granted'] = True
        session['secure_password_hash'] = self.real_password.password_hash
        session['secure_password_type'] = 'real'
        session.save()

    def test_matrix_view_access(self):
        """Probar acceso a la vista de matriz"""
        response = self.client.get(reverse('secure_data:matrix_view'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'secure_data/matrix_infinite.html')

    def test_update_cell(self):
        """Probar actualización de una celda"""
        data = {
            'row': 0,
            'col': 0,
            'value': 'Test Value'
        }
        response = self.client.post(
            reverse('secure_data:update_cell'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verificar que la celda se guardó
        cell = SecureDataMatrix.objects.get(
            password_hash=self.real_password.password_hash,
            row_index=0,
            col_index=0
        )
        self.assertEqual(
            cell.get_decrypted_value(self.real_password.password_hash),
            'Test Value'
        )

    def test_save_matrix(self):
        """Probar guardado completo de la matriz"""
        matrix_data = {
            '0': {
                '0': 'Value 1',
                '1': 'Value 2'
            },
            '1': {
                '0': 'Value 3',
                '1': 'Value 4'
            }
        }
        data = {'matrix_data': matrix_data}
        response = self.client.post(
            reverse('secure_data:save_matrix'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['cells_updated'], 4)

    def test_logout_secure(self):
        """Probar cierre de sesión seguro"""
        response = self.client.post(reverse('secure_data:logout_secure'))
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Verificar que la sesión se limpió
        session = self.client.session
        self.assertNotIn('secure_access_granted', session)
        self.assertNotIn('secure_password_hash', session)
        self.assertNotIn('secure_password_type', session)

class SecureMatrixJSTests(TestCase):
    """Pruebas de integración para las funcionalidades JavaScript"""
    
    def setUp(self):
        # Similar al setUp anterior
        self.user = User.objects.create_user(
            username='c.rodriguez',
            email='c.rodriguez@figbiz.net',
            password='TestPass123!',
            usr_2fa=True
        )
        self.client = Client()
        self.client.login(username='c.rodriguez', password='TestPass123!')
        
        # Configurar sesión segura
        session = self.client.session
        session['secure_access_granted'] = True
        session['secure_password_hash'] = 'test_hash'
        session['secure_password_type'] = 'real'
        session.save()

    def test_matrix_js_initialization(self):
        """Probar que la página carga con la configuración JS correcta"""
        response = self.client.get(reverse('secure_data:matrix_view'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar que los scripts necesarios están incluidos
        self.assertContains(response, 'x-data-spreadsheet.js')
        self.assertContains(response, 'undoAction')
        self.assertContains(response, 'redoAction')
        self.assertContains(response, 'saveMatrix')
        self.assertContains(response, 'logoutSecure')

    def test_matrix_buttons_presence(self):
        """Probar que los botones están presentes en el HTML"""
        response = self.client.get(reverse('secure_data:matrix_view'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar botones
        self.assertContains(response, 'undoBtn')
        self.assertContains(response, 'redoBtn')
        self.assertContains(response, 'Deshacer')
        self.assertContains(response, 'Rehacer')
        self.assertContains(response, 'Guardar')
        self.assertContains(response, 'Salir')

    def test_keyboard_shortcuts_setup(self):
        """Probar que los atajos de teclado están configurados"""
        response = self.client.get(reverse('secure_data:matrix_view'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar configuración de atajos
        self.assertContains(response, 'keydown')
        self.assertContains(response, 'ctrlKey')
        self.assertContains(response, 'metaKey')  # Para Mac
        self.assertContains(response, "key === 'z'")
        self.assertContains(response, "key === 'y'") 