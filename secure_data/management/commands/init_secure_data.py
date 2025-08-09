from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from secure_data.utils import initialize_demo_data

User = get_user_model()

class Command(BaseCommand):
    help = 'Inicializa el módulo de datos seguros con datos demo'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Iniciando configuración del módulo ultra-seguro...')
        )
        
        # Crear usuario autorizado si no existe
        user, created = User.objects.get_or_create(
            email='c.rodriguez@figbiz.net',
            defaults={
                'username': 'c.rodriguez',
                'first_name': 'Carlos',
                'last_name': 'Rodriguez',
                'is_active': True,
                'usr_2fa': True,
                'role': 'admin'
            }
        )
        
        if created:
            user.set_password('SecurePass2024!')
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Usuario autorizado creado: {user.email}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Usuario ya existe: {user.email}')
            )
        
        # Inicializar contraseñas secretas primero
        try:
            self.stdout.write('Inicializando contraseñas secretas...')
            from django.core.management import call_command
            call_command('init_secure_passwords')
            self.stdout.write(
                self.style.SUCCESS('Contraseñas secretas inicializadas')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error inicializando contraseñas: {str(e)}')
            )
            
        # Inicializar datos demo
        try:
            self.stdout.write('Inicializando datos demo...')
            initialize_demo_data()
            self.stdout.write(
                self.style.SUCCESS('Datos demo inicializados correctamente')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error inicializando datos demo: {str(e)}')
            )
            import traceback
            self.stdout.write(
                self.style.ERROR(f'Traceback: {traceback.format_exc()}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('¡Configuración completada!')
        )
        self.stdout.write(
            self.style.WARNING('IMPORTANTE: Revisar archivo passwords.txt para credenciales')
        )
