from django.test import TestCase
from django.urls import reverse
from .models import User

class UserModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            usr_name='testuser',
            user_password='testpassword',
            usr_2fa=False,
            usr_fecha_alta='2023-01-01',
            usr_fecha_baja=None,
            usr_estado='active',
            usr_password_recovery=False
        )

    def test_user_creation(self):
        self.assertEqual(self.user.usr_name, 'testuser')
        self.assertFalse(self.user.usr_2fa)
        self.assertEqual(self.user.usr_estado, 'active')

    def test_user_str(self):
        self.assertEqual(str(self.user), 'testuser')

class UserViewsTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            usr_name='testuser',
            user_password='testpassword',
            usr_2fa=False,
            usr_fecha_alta='2023-01-01',
            usr_fecha_baja=None,
            usr_estado='active',
            usr_password_recovery=False
        )

    def test_login_view(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 200)

    def test_registration_view(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password': 'newpassword'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful registration

    def test_password_reset_view(self):
        response = self.client.post(reverse('reset_password'), {
            'email': 'testuser@example.com'
        })
        self.assertEqual(response.status_code, 200)  # Assuming the view returns 200 on success

    def test_two_factor_auth_view(self):
        response = self.client.get(reverse('two_factor_auth'))
        self.assertEqual(response.status_code, 200)  # Check if the view loads correctly