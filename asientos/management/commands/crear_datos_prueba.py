"""
Management command para crear datos de prueba para el sistema de asientos contables
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
from datetime import date, timedelta

from empresas.models import Empresa
from perfiles.models import Perfil, PerfilPlanCuenta
from plan_cuentas.models import PlanCuenta, Cuenta
from asientos.models import Asiento
from asientos_detalle.models import AsientoDetalle

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea datos de prueba para el sistema de asientos contables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Elimina todos los datos existentes antes de crear los nuevos',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Eliminando datos existentes...')
            AsientoDetalle.objects.all().delete()
            Asiento.objects.all().delete()
            PerfilPlanCuenta.objects.all().delete()
            PlanCuenta.objects.all().delete()
            Perfil.objects.all().delete()
            Empresa.objects.all().delete()

        try:
            with transaction.atomic():
                self.crear_empresas()
                self.crear_perfiles()
                self.crear_plan_cuentas()
                self.asociar_cuentas_perfil()
                self.crear_usuarios()
                self.crear_asientos_ejemplo()
                
            self.stdout.write(
                self.style.SUCCESS('✅ Datos de prueba creados exitosamente')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creando datos de prueba: {str(e)}')
            )

    def crear_empresas(self):
        """Crear empresas de prueba"""
        self.stdout.write('Creando empresas...')
        
        empresa, created = Empresa.objects.get_or_create(
            id='DEFAULT',
            defaults={
                'nombre': 'Empresa Demo S.A.S',
                'type': 'Sociedad por Acciones Simplificada',
                'descripcion': 'Empresa de demostración para el sistema contable',
                'activa': True
            }
        )
        
        if created:
            self.stdout.write(f'  ✓ Empresa creada: {empresa.nombre}')
        else:
            self.stdout.write(f'  ⚠ Empresa ya existe: {empresa.nombre}')

    def crear_plan_cuentas(self):
        """Crear plan de cuentas básico"""
        self.stdout.write('Creando plan de cuentas...')
        
        empresa = Empresa.objects.get(id='DEFAULT')
        perfil = Perfil.objects.get(empresa='DEFAULT', secuencial=1)
        
        # Crear o obtener plan de cuentas general
        plan_cuentas, created = PlanCuenta.objects.get_or_create(
            empresa_id=empresa,
            descripcion='Plan de Cuentas General',
            defaults={}
        )
        
        if created:
            self.stdout.write(f'  ✓ Plan de cuentas creado: {plan_cuentas.descripcion}')
        
        cuentas = [
            # ACTIVOS
            ('1', 'ACTIVOS', '', 1),
            ('11', 'ACTIVO CORRIENTE', '1', 1),
            ('1105', 'CAJA', '11', 1),
            ('1110', 'BANCOS', '11', 1),
            ('1305', 'CLIENTES', '11', 1),
            ('1435', 'INVENTARIOS', '11', 1),
            
            # PASIVOS
            ('2', 'PASIVOS', '', 2),
            ('21', 'PASIVO CORRIENTE', '2', 2),
            ('2205', 'PROVEEDORES', '21', 2),
            ('2365', 'RETENCIÓN EN LA FUENTE', '21', 2),
            ('2367', 'RETENCIÓN DE IVA', '21', 2),
            
            # PATRIMONIO
            ('3', 'PATRIMONIO', '', 3),
            ('31', 'CAPITAL SOCIAL', '3', 3),
            ('3105', 'CAPITAL SUSCRITO Y PAGADO', '31', 3),
            ('36', 'RESULTADOS DEL EJERCICIO', '3', 3),
            ('3605', 'UTILIDAD DEL EJERCICIO', '36', 3),
            
            # INGRESOS
            ('4', 'INGRESOS', '', 4),
            ('41', 'INGRESOS OPERACIONALES', '4', 4),
            ('4135', 'COMERCIO AL POR MAYOR', '41', 4),
            ('4175', 'DEVOLUCIONES EN VENTAS', '41', 4),
            
            # GASTOS
            ('5', 'GASTOS', '', 5),
            ('51', 'GASTOS OPERACIONALES', '5', 5),
            ('5105', 'GASTOS DE PERSONAL', '51', 5),
            ('5115', 'GASTOS GENERALES', '51', 5),
        ]
        
        for codigocuenta, descripcion, cuentamadre, grupo in cuentas:
            cuenta_creada, created = Cuenta.objects.get_or_create(
                codigocuenta=codigocuenta,
                plan_cuentas_id=plan_cuentas,
                empresa_id=empresa,
                defaults={
                    'cuenta': codigocuenta,  # Usar codigocuenta como valor de cuenta también
                    'descripcion': descripcion,
                    'cuentamadre': cuentamadre if cuentamadre else None,
                    'grupo': grupo,
                    'cuentas_id_madre': cuentamadre if cuentamadre else None,
                }
            )
            
            if created:
                self.stdout.write(f'  ✓ Cuenta creada: {codigocuenta} - {descripcion}')

    def crear_perfiles(self):
        """Crear perfiles contables"""
        self.stdout.write('Creando perfiles contables...')
        
        perfil, created = Perfil.objects.get_or_create(
            empresa='DEFAULT',
            secuencial=1,
            defaults={
                'descripcion': 'Perfil General',
                'vigencia': 'S'
            }
        )
        
        if created:
            self.stdout.write(f'  ✓ Perfil creado: {perfil.descripcion}')

    def asociar_cuentas_perfil(self):
        """Asociar cuentas al perfil (llamar después de crear cuentas)"""
        self.stdout.write('Asociando cuentas al perfil...')
        
        perfil = Perfil.objects.get(empresa='DEFAULT', secuencial=1)
        
        # Asociar cuentas individuales al perfil
        cuentas = Cuenta.objects.filter(empresa_id__id='DEFAULT')
        asociadas = 0
        
        for cuenta in cuentas:
            # Verificar que codigocuenta no sea None
            if not cuenta.codigocuenta:
                continue
                
            # Determinar polaridad según tipo de cuenta
            if cuenta.codigocuenta.startswith(('1', '5')):  # ACTIVO, GASTO
                polaridad = '+'
            else:  # PASIVO, PATRIMONIO, INGRESO
                polaridad = '-'
            
            perfil_cuenta, created = PerfilPlanCuenta.objects.get_or_create(
                perfil_id=perfil,
                cuentas_id=cuenta,
                defaults={
                    'empresa': 'DEFAULT',
                    'polaridad': polaridad
                }
            )
            
            if created:
                asociadas += 1
        
        self.stdout.write(f'  ✓ {asociadas} cuentas asociadas al perfil')

    def crear_usuarios(self):
        """Crear usuarios de prueba"""
        self.stdout.write('Creando usuarios...')
        
        # Usuario supervisor
        supervisor, created = User.objects.get_or_create(
            username='supervisor',
            defaults={
                'first_name': 'Usuario',
                'last_name': 'Supervisor',
                'email': 'supervisor@demo.com',
                'is_staff': True,
                'is_active': True,
                'role': 'supervisor',
                'usr_estado': True
            }
        )
        
        if created:
            supervisor.set_password('supervisor123')
            supervisor.save()
            self.stdout.write(f'  ✓ Usuario supervisor creado: supervisor/supervisor123')
        else:
            self.stdout.write(f'  ⚠ Usuario supervisor ya existe')

    def crear_asientos_ejemplo(self):
        """Crear asientos contables de ejemplo"""
        self.stdout.write('Creando asientos de ejemplo...')
        
        try:
            from datetime import date, timedelta
            from decimal import Decimal
            
            perfil = Perfil.objects.get(empresa='DEFAULT', secuencial=1)
            
            # Asiento 1: Venta de mercancía
            asiento1 = Asiento.objects.create(
                fecha=date.today(),
                empresa='DEFAULT',
                id_perfil=perfil
            )
            
            # Detalles del asiento 1
            caja = Cuenta.objects.get(cuenta='1105', empresa_id__id='DEFAULT')
            ventas = Cuenta.objects.get(cuenta='4135', empresa_id__id='DEFAULT')
            
            AsientoDetalle.objects.create(
                asiento=asiento1,
                cuenta=caja,
                valor=1000000.00,
                polaridad='+',
                tipo_cuenta='DEBE'
            )
            
            AsientoDetalle.objects.create(
                asiento=asiento1,
                cuenta=ventas,
                valor=1000000.00,
                polaridad='-',
                tipo_cuenta='HABER'
            )
            
            self.stdout.write(f'  ✓ Asiento creado: {asiento1.fecha}')
            
            # Asiento 2: Compra de inventario
            asiento2 = Asiento.objects.create(
                fecha=date.today() - timedelta(days=1),
                empresa='DEFAULT',
                id_perfil=perfil
            )
            
            # Detalles del asiento 2
            inventarios = Cuenta.objects.get(cuenta='1435', empresa_id__id='DEFAULT')
            proveedores = Cuenta.objects.get(cuenta='2205', empresa_id__id='DEFAULT')
            
            AsientoDetalle.objects.create(
                asiento=asiento2,
                cuenta=inventarios,
                valor=500000.00,
                polaridad='+',
                tipo_cuenta='DEBE'
            )
            
            AsientoDetalle.objects.create(
                asiento=asiento2,
                cuenta=proveedores,
                valor=500000.00,
                polaridad='-',
                tipo_cuenta='HABER'
            )
            
            self.stdout.write(f'  ✓ Asiento creado: {asiento2.fecha}')
            
        except Exception as e:
            self.stdout.write(f'  ❌ Error creando asientos: {str(e)}')
            
            self.stdout.write(f'  ✓ Asiento creado: {asiento2.descripcion}')
            
        except Exception as e:
            self.stdout.write(f'  ❌ Error creando asientos: {str(e)}')
