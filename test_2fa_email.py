#!/usr/bin/env python3
import os
import sys
import django

# Configurar el entorno de Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asientos_contables.settings')
django.setup()

from django.contrib.auth import get_user_model
from secure_data.utils import send_2fa_email

User = get_user_model()

try:
    # Buscar el usuario específico
    user = User.objects.get(email='c.rodriguez@figbiz.net')
    print(f"Usuario encontrado: {user.email}")
    
    # Intentar enviar el código 2FA
    print("Intentando enviar código 2FA...")
    result = send_2fa_email(user)
    
    if result:
        print("✅ Código 2FA enviado exitosamente!")
    else:
        print("❌ Error al enviar código 2FA")
        
except User.DoesNotExist:
    print("❌ Usuario c.rodriguez@figbiz.net no encontrado")
except Exception as e:
    print(f"❌ Error: {str(e)}")
