#!/bin/bash

# Script rápido para configurar admin y módulo seguro con Hogemail
# ================================================================

echo "🚀 CONFIGURACIÓN RÁPIDA - ADMIN + MÓDULO SEGURO"
echo "==============================================="

# Aplicar migraciones básicas
echo "🗄️  Aplicando migraciones..."
python manage.py migrate

# Crear superusuario admin
echo "👑 Creando superusuario admin..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice

User = get_user_model()

# Crear superusuario
admin_email = 'admin@hogemail.com'
admin_user, created = User.objects.get_or_create(
    email=admin_email,
    defaults={
        'username': 'admin',
        'first_name': 'Administrador',
        'last_name': 'Sistema',
        'is_active': True,
        'is_staff': True,
        'is_superuser': True,
        'usr_2fa': True,
        'role': 'admin'
    }
)

if created or True:  # Siempre actualizar contraseña
    admin_user.set_password('admin123')
    admin_user.save()
    print(f"✅ Superusuario configurado: {admin_user.email}")

# Crear dispositivo 2FA para admin
device, created = TOTPDevice.objects.get_or_create(
    user=admin_user,
    name='default',
    defaults={'confirmed': True}
)

print(f"📱 Dispositivo 2FA: {'creado' if created else 'ya existe'}")

# Crear usuario de prueba para módulo seguro
test_email = 'test@hogemail.com'
test_user, created = User.objects.get_or_create(
    email=test_email,
    defaults={
        'username': 'test',
        'first_name': 'Usuario',
        'last_name': 'Prueba',
        'is_active': True,
        'usr_2fa': True,
        'role': 'user'
    }
)

if created or True:  # Siempre actualizar contraseña
    test_user.set_password('test123')
    test_user.save()
    print(f"✅ Usuario de prueba configurado: {test_user.email}")

# Crear dispositivo 2FA para usuario de prueba
device_test, created = TOTPDevice.objects.get_or_create(
    user=test_user,
    name='default',
    defaults={'confirmed': True}
)

print(f"📱 Dispositivo 2FA prueba: {'creado' if created else 'ya existe'}")

EOF

# Inicializar módulo seguro si existe
if [ -f "manage.py" ] && python manage.py help | grep -q "init_secure_data"; then
    echo "🛡️  Inicializando módulo seguro..."
    python manage.py makemigrations secure_data 2>/dev/null || true
    python manage.py migrate
    
    # Ejecutar comando con manejo de errores mejorado
    if python manage.py init_secure_data; then
        echo "✅ Módulo seguro inicializado correctamente"
    else
        echo "⚠️  Hubo algunos problemas inicializando el módulo seguro (es normal si ya existe)"
    fi
else
    echo "⚠️  Módulo seguro no encontrado o comando no disponible"
fi

echo ""
echo "🎉 CONFIGURACIÓN COMPLETADA!"
echo "============================"
echo ""
echo "👑 SUPERUSUARIO ADMIN:"
echo "• Email: admin@hogemail.com"
echo "• Password: admin123"
echo "• URL Admin: http://localhost:8000/admin/"
echo ""
echo "👤 USUARIO DE PRUEBA:"
echo "• Email: test@hogemail.com"
echo "• Password: test123"
echo "• URL Login: http://localhost:8000/accounts/login/"
echo ""
echo "🛡️  MÓDULO SEGURO:"
echo "• URL: http://localhost:8000/secure/xk9mz8p4q7w3n6v2/"
echo ""
echo "🚀 Para iniciar el servidor:"
echo "python manage.py runserver"
echo ""
echo "📱 NOTA: 2FA está habilitado pero con dispositivos confirmados"
echo "   para facilitar las pruebas"
echo ""
