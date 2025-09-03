from django.test import TestCase
from django.contrib.auth import get_user_model
from empresas.models import Empresa
from perfiles.models import Perfil
from plan_cuentas.models import PlanCuenta, Cuenta

class CuentaModelTests(TestCase):
    def setUp(self):
        # Minimal fixtures
        self.empresa = Empresa.objects.create(nombre="Acme", nit="123", activa=True)
        self.perfil = Perfil.objects.create(nombre="General")
        self.plan = PlanCuenta.objects.create(empresa=self.empresa, descripcion="Plan 2025", perfil=self.perfil)

    def test_cuenta_madre_nullable_and_same_plan(self):
        c1 = Cuenta.objects.create(cuenta="1000", descripcion="Caja", plan_cuentas=self.plan)
        # cuenta_madre may be null
        self.assertIsNone(c1.cuenta_madre)
        # child referencing same plan
        c2 = Cuenta.objects.create(cuenta="1100", descripcion="Caja Menor", plan_cuentas=self.plan, cuenta_madre=c1)
        self.assertEqual(c2.cuenta_madre_id, c1.id)

    def test_perfil_inherits_from_plan_when_missing(self):
        c = Cuenta.objects.create(cuenta="2000", descripcion="Bancos", plan_cuentas=self.plan)
        self.assertEqual(c.perfil_id, self.perfil.id)
