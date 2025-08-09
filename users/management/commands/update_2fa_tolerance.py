from django.core.management.base import BaseCommand
from django_otp.plugins.otp_totp.models import TOTPDevice

class Command(BaseCommand):
    help = 'Actualiza la tolerancia de todos los dispositivos TOTP existentes para mayor seguridad'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tolerance', 
            type=int, 
            default=1,
            help='Nivel de tolerancia (1 = 90 segundos total, 2 = 150 segundos total, etc.)'
        )

    def handle(self, *args, **options):
        tolerance = options['tolerance']
        
        # Obtener todos los dispositivos TOTP
        devices = TOTPDevice.objects.all()
        
        if not devices.exists():
            self.stdout.write(
                self.style.WARNING('⚠️  No se encontraron dispositivos TOTP para actualizar')
            )
            return
        
        self.stdout.write(f'🔍 Encontrados {devices.count()} dispositivos TOTP')
        
        updated_count = 0
        for device in devices:
            old_tolerance = device.tolerance
            old_drift = device.drift
            
            # Actualizar configuración
            device.tolerance = tolerance
            device.drift = 0  # Sin deriva temporal
            device.save()
            
            updated_count += 1
            
            self.stdout.write(
                f'✅ Dispositivo "{device.name}" (Usuario: {device.user.username})'
            )
            self.stdout.write(
                f'   - Tolerancia: {old_tolerance} → {device.tolerance}'
            )
            self.stdout.write(
                f'   - Deriva: {old_drift} → {device.drift}'
            )
        
        total_validity_seconds = 30 + (tolerance * 30 * 2)  # Tiempo actual + ventanas antes/después
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(f'🎉 Se actualizaron {updated_count} dispositivos TOTP')
        )
        self.stdout.write('')
        self.stdout.write('📊 Configuración aplicada:')
        self.stdout.write(f'   - Tolerancia: ±{tolerance} ventanas')
        self.stdout.write(f'   - Deriva temporal: 0 (deshabilitada)')
        self.stdout.write(f'   - Validez total: ~{total_validity_seconds} segundos')
        self.stdout.write('')
        self.stdout.write(
            self.style.WARNING('⚡ Los usuarios necesitarán usar códigos más actualizados de sus apps')
        )
