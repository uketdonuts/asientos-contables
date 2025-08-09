import unittest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import SecureDataMatrix
import hashlib

User = get_user_model()

class SecureDataTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='c.rodriguez@figbiz.net',
            password='testpass123'
        )
        self.client = Client()
    
    def test_unauthorized_access(self):
        """Test que usuarios no autorizados no pueden acceder"""
        unauthorized_user = User.objects.create_user(
            username='hacker',
            email='hacker@example.com',
            password='hackpass'
        )
        self.client.login(username='hacker', password='hackpass')
        
        response = self.client.get(reverse('secure_data:access'))
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_encryption_decryption(self):
        """Test del sistema de encriptación"""
        test_data = "Datos ultra secretos"
        password_hash = "testhash123"
        
        encrypted_value, salt = SecureDataMatrix.encrypt_data(test_data, password_hash)
        decrypted_value = SecureDataMatrix.decrypt_data(encrypted_value, salt, password_hash)
        
        self.assertEqual(test_data, decrypted_value)
    
    def test_wrong_password_decryption(self):
        """Test que datos no se pueden desencriptar con contraseña incorrecta"""
        test_data = "Datos secretos"
        correct_password = "correct_hash"
        wrong_password = "wrong_hash"
        
        encrypted_value, salt = SecureDataMatrix.encrypt_data(test_data, correct_password)
        decrypted_value = SecureDataMatrix.decrypt_data(encrypted_value, salt, wrong_password)
        
        self.assertIsNone(decrypted_value)
