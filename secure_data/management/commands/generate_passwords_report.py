from django.core.management.base import BaseCommand
from secure_data.models import SecurePassword
import datetime

class Command(BaseCommand):
    help = 'Genera un reporte actualizado de las contraseñas secretas'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Generando reporte de contraseñas secretas...')
        )
        
        # Obtener todas las contraseñas activas
        decoy_passwords = SecurePassword.objects.filter(
            password_type='decoy', 
            is_active=True
        ).order_by('password_text')
        
        real_passwords = SecurePassword.objects.filter(
            password_type='real', 
            is_active=True
        ).order_by('password_text')
        
        # Generar el contenido del archivo
        content = f"""# CONTRASEÑAS DEL MÓDULO ULTRA-SEGURO
# =====================================
# CONFIDENCIAL - SOLO PARA c.rodriguez@figbiz.net
# Fecha de generación: {datetime.date.today()}

## INFORMACIÓN IMPORTANTE:
- Usuario autorizado: c.rodriguez@figbiz.net
- URL de acceso: https://tu-dominio.com/secure/xk9mz8p4q7w3n6v2/
- Requiere 2FA de email + aplicación authenticator

## CONTRASEÑAS FALSAS (Muestran información pública/decoy):
"""
        
        for i, pwd in enumerate(decoy_passwords, 1):
            content += f"{i}. {pwd.password_text}\n"
        
        content += "\n## CONTRASEÑAS REALES (Muestran información ultra-secreta):\n"
        
        for i, pwd in enumerate(real_passwords, 1):
            content += f"{i}. {pwd.password_text}\n"
        
        content += """
## NOTAS DE SEGURIDAD:
- Todas las contraseñas son case-sensitive
- Los datos están encriptados con AES-256 + PBKDF2
- Cada acceso queda registrado con IP, timestamp y user agent
- La URL secreta no aparece en ningún menú del sistema
- Solo el email autorizado puede acceder al módulo

## DATOS DEMO INICIALIZADOS:
### Información Falsa (contraseñas decoy):
- Proyectos ficticios con montos bajos
- Clientes genéricos
- Estados de "Pendiente" y "Completado"

### Información Real (contraseñas reales):
- OPERACIÓN ALPHA - $2,500,000 - CONFIDENCIAL
- CONTACTO BETA - $5,800,000 - ULTRA-SECRETO  
- PROYECTO GAMMA - $12,000,000 - ALTO RIESGO

## INSTRUCCIONES DE USO:
1. Logearse como c.rodriguez@figbiz.net
2. Navegar a /secure/xk9mz8p4q7w3n6v2/
3. Ingresar una de las 6 contraseñas
4. Ingresar código 2FA del email
5. Ingresar código 2FA de la app authenticator
6. Editar la matriz tipo Excel
7. Los cambios se guardan automáticamente

¡MANTENER ESTE ARCHIVO EN LUGAR SEGURO!
"""
        
        # Escribir el archivo
        with open('passwords.txt', 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.stdout.write(
            self.style.SUCCESS('passwords.txt actualizado correctamente')
        )
        
        # Mostrar resumen
        self.stdout.write('')
        self.stdout.write(f"Contraseñas DECOY: {decoy_passwords.count()}")
        self.stdout.write(f"Contraseñas REALES: {real_passwords.count()}")
        self.stdout.write(f"Total: {decoy_passwords.count() + real_passwords.count()}")
