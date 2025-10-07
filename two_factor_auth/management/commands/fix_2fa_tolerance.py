from django.core.management.base import BaseCommand
from django_otp.plugins.otp_totp.models import TOTPDevice


class Command(BaseCommand):
    help = 'Actualiza la tolerancia de dispositivos 2FA existentes'

    def handle(self, *args, **options):
        # Actualizar todos los dispositivos existentes
        devices_updated = 0
        for device in TOTPDevice.objects.all():
            if device.tolerance is None or device.tolerance < 20:
                device.tolerance = 5
                device.save(update_fields=['tolerance'])
                devices_updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Actualizado dispositivo {device.name} para usuario {device.user.username}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Proceso completado. {devices_updated} dispositivos actualizados.'
            )
        )