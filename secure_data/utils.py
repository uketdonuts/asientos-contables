from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
import random
import string
import hashlib
from django.core.cache import cache
import logging

User = get_user_model()
logger = logging.getLogger('secure_data')

def generate_email_2fa_code():
    """Genera un código 2FA de 6 dígitos"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def send_2fa_email(user):
    """Envía código 2FA por email"""
    if user.email != 'c.rodriguez@figbiz.net':
        logger.warning(f"[2FA][EMAIL] Email no autorizado: {user.email}")
        return False
    
    code = generate_email_2fa_code()
    # No loguear el código completo en texto claro; mostrar solo últimos 2 dígitos
    masked_code = f"****{code[-2:]}"
    
    # Guardar código en cache por 2 minutos (para cumplir con el estándar del sistema)
    cache_key = f"email_2fa_{user.usr_id}"
    cache.set(cache_key, code, 120)  # 2 minutos
    logger.info(f"[2FA][EMAIL] Código generado {masked_code} y guardado en cache (key={cache_key}) para user_id={user.usr_id}")
    
    try:
        logger.info(
            f"[2FA][EMAIL] Enviando email a {user.email} (host={getattr(settings, 'EMAIL_HOST', None)}, "
            f"port={getattr(settings, 'EMAIL_PORT', None)}, from={getattr(settings, 'DEFAULT_FROM_EMAIL', None)})"
        )

        # Construir enlace directo al acceso ultra-seguro
        # Nota: la ruta se define estáticamente en secure_data/urls.py
        secure_path = reverse('secure_data:access')  # '/secure/xk9mz8p4q7w3n6v2/'
        # reverse devuelve '/secure/' + ... gracias a include('secure_data.urls') en urls raíz
        # Pero como el patrón exacto está en secure_data/urls.py, reverse('secure_data:access') devolverá '/secure/xk9mz8p4q7w3n6v2/'
        full_secure_url = f"{settings.SITE_BASE_URL}{secure_path}"

        send_mail(
            subject='Código de Verificación - Acceso Seguro',
            message=(
                "Código de verificación para acceso al módulo seguro:\n\n"
                f"{code}\n\n"
                "Este código expira en 2 minutos.\n\n"
                "Accede directamente con este enlace (requiere autenticación previa):\n"
                f"{full_secure_url}\n\n"
                "Si no solicitaste este código, ignora este email."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info("[2FA][EMAIL] Email enviado exitosamente")
        return True
    except Exception as e:
        logger.exception(f"[2FA][EMAIL] Error al enviar email: {str(e)}")
        return False

def validate_email_2fa(user, code):
    """Valida el código 2FA del email"""
    if user.email != 'c.rodriguez@figbiz.net':
        logger.warning(f"[2FA][EMAIL] Validación rechazada: email no autorizado {user.email}")
        return False
    
    cache_key = f"email_2fa_{user.usr_id}"
    stored_code = cache.get(cache_key)
    masked_input = f"****{code[-2:]}" if code else "(vacío)"

    if stored_code:
        masked_stored = f"****{stored_code[-2:]}"
        if stored_code == code:
            # Invalidar código después de uso
            cache.delete(cache_key)
            logger.info(f"[2FA][EMAIL] Código válido {masked_input} para user_id={user.usr_id}; invalidado tras uso")
            return True
        else:
            logger.warning(
                f"[2FA][EMAIL] Código inválido para user_id={user.usr_id}: recibido {masked_input}, esperado {masked_stored}"
            )
            return False
    else:
        logger.warning(
            f"[2FA][EMAIL] No se encontró código en cache para user_id={user.usr_id} (key={cache_key}); recibido {masked_input}"
        )
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
