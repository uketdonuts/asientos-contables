from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice

User = get_user_model()

class Command(BaseCommand):
    help = 'Reinicializa el 2FA para un usuario específico. Después de resetear, el usuario tendrá códigos válidos por ~90 segundos (tolerancia estricta)'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email del usuario')
        parser.add_argument('--username', type=str, help='Username del usuario')

    def handle(self, *args, **options):
        email = options.get('email')
        username = options.get('username')
        
        if not email and not username:
            self.stdout.write(
                self.style.ERROR('Debe proporcionar --email o --username')
            )
            return
        
        try:
            # Buscar usuario
            if email:
                user = User.objects.get(email=email)
            else:
                user = User.objects.get(username=username)
            
            self.stdout.write(f'🔍 Usuario encontrado: {user.username} ({user.email})')
            
            # Verificar dispositivos existentes
            devices = TOTPDevice.objects.filter(user=user)
            self.stdout.write(f'📱 Dispositivos 2FA existentes: {devices.count()}')
            
            # Mostrar dispositivos existentes
            if devices.exists():
                for device in devices:
                    self.stdout.write(f'   - Dispositivo: {device.name} (Confirmado: {device.confirmed})')
                
                # Eliminar todos los dispositivos TOTP
                deleted_count = devices.delete()[0]
                self.stdout.write(
                    self.style.SUCCESS(f'🗑️  Eliminados {deleted_count} dispositivos TOTP')
                )
            else:
                self.stdout.write('📱 No hay dispositivos TOTP para eliminar')
            
            # Restablecer el campo usr_2fa a False
            original_2fa_status = user.usr_2fa
            user.usr_2fa = False
            user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'🔄 Campo usr_2fa cambiado de {original_2fa_status} a {user.usr_2fa}')
            )
            
            # Limpiar códigos de recuperación
            if hasattr(user, 'usr_recovery_codes') and user.usr_recovery_codes:
                user.usr_recovery_codes = None
                user.save()
                self.stdout.write(
                    self.style.SUCCESS('🔑 Códigos de recuperación eliminados')
                )
            else:
                self.stdout.write('🔑 No había códigos de recuperación')
            
            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS('✅ 2FA completamente reinicializado para el usuario')
            )
            
            self.stdout.write('\n📋 Estado final:')
            self.stdout.write(f'   - Username: {user.username}')
            self.stdout.write(f'   - Email: {user.email}')
            self.stdout.write(f'   - usr_2fa: {user.usr_2fa}')
            self.stdout.write(f'   - Dispositivos TOTP: {TOTPDevice.objects.filter(user=user).count()}')
            self.stdout.write(f'   - Códigos de recuperación: {"Sí" if user.usr_recovery_codes else "No"}')
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING('🔔 El usuario deberá configurar 2FA nuevamente en el próximo login')
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Usuario no encontrado')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )
