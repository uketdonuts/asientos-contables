from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
import random
import string
import hashlib
from django.core.cache import cache

User = get_user_model()

def generate_email_2fa_code():
    """Genera un código 2FA de 6 dígitos"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def send_2fa_email(user):
    """Envía código 2FA por email"""
    if user.email != 'c.rodriguez@figbiz.net':
        print(f"[DEBUG] Email no autorizado: {user.email}")
        return False
    
    code = generate_email_2fa_code()
    print(f"[DEBUG] Código generado: {code}")
    
    # Guardar código en cache por 2 minutos (para cumplir con el estándar del sistema)
    cache_key = f"email_2fa_{user.usr_id}"
    cache.set(cache_key, code, 120)  # 2 minutos
    print(f"[DEBUG] Código guardado en cache con key: {cache_key}")
    
    try:
        print(f"[DEBUG] Intentando enviar email a: {user.email}")
        print(f"[DEBUG] Configuración EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"[DEBUG] Configuración EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"[DEBUG] Configuración DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        
        send_mail(
            subject='Código de Verificación - Acceso Seguro',
            message=f'''
            Código de verificación para acceso al módulo seguro:
            
            {code}
            
            Este código expira en 2 minutos.
            
            Si no solicitaste este código, ignora este email.
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        print(f"[DEBUG] Email enviado exitosamente")
        return True
    except Exception as e:
        print(f"[DEBUG] Error al enviar email: {str(e)}")
        import traceback
        print(f"[DEBUG] Traceback completo: {traceback.format_exc()}")
        return False

def validate_email_2fa(user, code):
    """Valida el código 2FA del email"""
    if user.email != 'c.rodriguez@figbiz.net':
        return False
    
    cache_key = f"email_2fa_{user.usr_id}"
    stored_code = cache.get(cache_key)
    
    if stored_code and stored_code == code:
        # Invalidar código después de uso
        cache.delete(cache_key)
        return True
    
    return False

def initialize_demo_data():
    """Inicializa datos demo para las contraseñas de forma idempotente"""
    from .models import SecureDataMatrix, SecurePassword
    
    # Obtener contraseñas desde la base de datos
    decoy_passwords = SecurePassword.objects.filter(
        password_type='decoy', 
        is_active=True
    ).values_list('password_text', flat=True)
    
    real_passwords = SecurePassword.objects.filter(
        password_type='real', 
        is_active=True
    ).values_list('password_text', flat=True)
    
    # Datos falsos para contraseñas decoy
    decoy_data = {
        (0, 0): "Proyecto A", (0, 1): "125,000", (0, 2): "Pendiente",
        (1, 0): "Cliente B", (1, 1): "89,500", (1, 2): "Completado",
        (2, 0): "Inversión C", (2, 1): "250,000", (2, 2): "En Progreso",
    }
    
    # Datos reales para contraseñas reales
    real_data = {
        (0, 0): "OPERACIÓN ALPHA", (0, 1): "2,500,000", (0, 2): "CONFIDENCIAL",
        (1, 0): "CONTACTO BETA", (1, 1): "5,800,000", (1, 2): "ULTRA-SECRETO",
        (2, 0): "PROYECTO GAMMA", (2, 1): "12,000,000", (2, 2): "ALTO RIESGO",
    }
    
    created_count = 0
    existing_count = 0
    
    # Crear datos para contraseñas decoy
    for password in decoy_passwords:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        for (row, col), value in decoy_data.items():
            data_obj, created = SecureDataMatrix.objects.get_or_create(
                password_hash=password_hash,
                row_index=row,
                col_index=col,
                defaults={'data_type': 'decoy'}
            )
            if created:
                data_obj.set_encrypted_value(value, password_hash)
                data_obj.save()
                created_count += 1
            else:
                existing_count += 1
    
    # Crear datos para contraseñas reales
    for password in real_passwords:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        for (row, col), value in real_data.items():
            data_obj, created = SecureDataMatrix.objects.get_or_create(
                password_hash=password_hash,
                row_index=row,
                col_index=col,
                defaults={'data_type': 'real'}
            )
            if created:
                data_obj.set_encrypted_value(value, password_hash)
                data_obj.save()
                created_count += 1
            else:
                existing_count += 1
    
    print(f"✅ Datos seguros: {created_count} nuevos, {existing_count} ya existían")
