from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

try:
    from django_otp.plugins.otp_totp.models import TOTPDevice
except Exception:
    TOTPDevice = None


class Command(BaseCommand):
    help = 'Reinicializa el 2FA para un usuario específico. Elimina dispositivos TOTP si django-otp está instalado y resetea el flag usr_2fa.'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email del usuario')
        parser.add_argument('--username', type=str, help='Username del usuario')

    def handle(self, *args, **options):
        email = options.get('email')
        username = options.get('username')

        if not email and not username:
            self.stdout.write(self.style.ERROR('Debe proporcionar --email o --username'))
            return

        try:
            if email:
                user = User.objects.get(email=email)
            else:
                user = User.objects.get(username=username)

            self.stdout.write(f'🔍 Usuario encontrado: {user.username} ({user.email})')

            # Si django-otp está disponible, eliminar dispositivos TOTP
            if TOTPDevice is not None:
                devices = TOTPDevice.objects.filter(user=user)
                self.stdout.write(f'📱 Dispositivos 2FA existentes: {devices.count()}')
                if devices.exists():
                    for device in devices:
                        self.stdout.write(f'   - Dispositivo: {getattr(device, "name", "<sin nombre>")} (Confirmado: {getattr(device, "confirmed", False)})')
                    deleted_count = devices.delete()[0]
                    self.stdout.write(self.style.SUCCESS(f'🗑️  Eliminados {deleted_count} dispositivos TOTP'))
                else:
                    self.stdout.write('📱 No hay dispositivos TOTP para eliminar')
            else:
                self.stdout.write('ℹ️ django-otp no está instalado; salto eliminación de dispositivos TOTP')

            # Restablecer el campo usr_2fa a False
            original_2fa_status = getattr(user, 'usr_2fa', None)
            user.usr_2fa = False
            user.save()
            self.stdout.write(self.style.SUCCESS(f'🔄 Campo usr_2fa cambiado de {original_2fa_status} a {user.usr_2fa}'))

            # Limpiar códigos de recuperación si existen
            if hasattr(user, 'usr_recovery_codes') and user.usr_recovery_codes:
                user.usr_recovery_codes = None
                user.save()
                self.stdout.write(self.style.SUCCESS('🔑 Códigos de recuperación eliminados'))
            else:
                self.stdout.write('🔑 No había códigos de recuperación')

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✅ 2FA reinicializado para el usuario'))
            self.stdout.write('\n📋 Estado final:')
            self.stdout.write(f'   - Username: {user.username}')
            self.stdout.write(f'   - Email: {user.email}')
            self.stdout.write(f'   - usr_2fa: {user.usr_2fa}')
            if TOTPDevice is not None:
                self.stdout.write(f'   - Dispositivos TOTP: {TOTPDevice.objects.filter(user=user).count()}')
            else:
                self.stdout.write('   - Dispositivos TOTP: (no verificado, django-otp ausente)')
            self.stdout.write(f'   - Códigos de recuperación: {"Sí" if getattr(user, "usr_recovery_codes", None) else "No"}')
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('🔔 El usuario deberá configurar 2FA nuevamente en el próximo login'))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ Usuario no encontrado'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
