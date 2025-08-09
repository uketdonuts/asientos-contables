from django.core.management.base import BaseCommand
from secure_data.models import SecurePassword

class Command(BaseCommand):
    help = 'Inicializa las contraseñas secretas del módulo ultra-seguro'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Inicializando contraseñas secretas...')
        )
        
        # Contraseñas decoy (información falsa/pública)
        decoy_passwords = [
            {
                'password_text': 'DataView2024!',
                'description': 'Contraseña para datos públicos/demo - Proyectos ficticios',
                'password_type': 'decoy'
            },
            {
                'password_text': 'SecureInfo#99',
                'description': 'Contraseña para datos públicos/demo - Información genérica',
                'password_type': 'decoy'
            },
            {
                'password_text': 'AccessMatrix@1',
                'description': 'Contraseña para datos públicos/demo - Matriz básica',
                'password_type': 'decoy'
            }
        ]
        
        # Contraseñas reales (información confidencial)
        real_passwords = [
            {
                'password_text': 'Qwerty01*+',
                'description': 'Contraseña para datos ultra-secretos - Operaciones Alpha',
                'password_type': 'real'
            },
            {
                'password_text': 'TrueInfo#Secret99',
                'description': 'Contraseña para datos ultra-secretos - Contactos Beta',
                'password_type': 'real'
            },
            {
                'password_text': 'AuthMatrix@Real1',
                'description': 'Contraseña para datos ultra-secretos - Proyectos Gamma',
                'password_type': 'real'
            }
        ]
        
        created_count = 0
        existing_count = 0
        
        # Crear contraseñas decoy
        for pwd_data in decoy_passwords:
            password_obj, created = SecurePassword.objects.get_or_create(
                password_text=pwd_data['password_text'],
                defaults={
                    'description': pwd_data['description'],
                    'password_type': pwd_data['password_type'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"  ✅ Creada: {pwd_data['password_text']} ({pwd_data['password_type']})")
            else:
                existing_count += 1
                self.stdout.write(f"  ⚠️  Ya existe: {pwd_data['password_text']}")
        
        # Crear contraseñas reales
        for pwd_data in real_passwords:
            password_obj, created = SecurePassword.objects.get_or_create(
                password_text=pwd_data['password_text'],
                defaults={
                    'description': pwd_data['description'],
                    'password_type': pwd_data['password_type'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"  ✅ Creada: {pwd_data['password_text']} ({pwd_data['password_type']})")
            else:
                existing_count += 1
                self.stdout.write(f"  ⚠️  Ya existe: {pwd_data['password_text']}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Proceso completado: {created_count} nuevas, {existing_count} existentes')
        )
        
        # Mostrar resumen
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('=== RESUMEN DE CONTRASEÑAS SECRETAS ==='))
        
        decoy_count = SecurePassword.objects.filter(password_type='decoy', is_active=True).count()
        real_count = SecurePassword.objects.filter(password_type='real', is_active=True).count()
        
        self.stdout.write(f"Contraseñas DECOY activas: {decoy_count}")
        self.stdout.write(f"Contraseñas REALES activas: {real_count}")
        self.stdout.write(f"Total de contraseñas activas: {decoy_count + real_count}")
