from django.test import TestCase
from django.core import mail

class SMTPTest(TestCase):
    def test_smtp_email_sending(self):
        # Enviar un correo de prueba
        mail.send_mail(
            subject='Test Email',
            message='This is a test email.',
            from_email='test@example.com',
            recipient_list=['recipient@example.com']
        )

        # Verificar que se haya enviado un correo
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Test Email')
        self.assertEqual(mail.outbox[0].body, 'This is a test email.')
        self.assertIn('recipient@example.com', mail.outbox[0].to)
