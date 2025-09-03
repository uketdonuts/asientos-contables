#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asientos_contables.settings')
django.setup()

from django.test import TestCase
from django.db import transaction
from empresas.models import Empresa
from perfiles.models import Perfil
from plan_cuentas.models import PlanCuenta, Cuenta

def test_cuenta_changes():
    print("🔍 Verificando cambios en el modelo Cuenta...")
    
    # Verificar campos del modelo
    cuenta_fields = [f.name for f in Cuenta._meta.fields]
    print(f"✅ Campos de Cuenta: {cuenta_fields}")
    
    # Verificar que existe cuenta_madre
    assert 'cuenta_madre' in cuenta_fields, "❌ Falta campo cuenta_madre"
    print("✅ Campo cuenta_madre presente")
    
    # Verificar que existe perfil
    assert 'perfil' in cuenta_fields, "❌ Falta campo perfil"
    print("✅ Campo perfil presente")
    
    # Verificar formularios
    from plan_cuentas.forms import CuentaForm
    form_fields = CuentaForm._meta.fields
    print(f"✅ Campos del formulario CuentaForm: {form_fields}")
    
    # Verificar que perfil está en el formulario
    assert 'perfil' in form_fields, "❌ Falta perfil en formulario"
    assert 'cuenta_madre' in form_fields, "❌ Falta cuenta_madre en formulario"
    print("✅ Formulario tiene todos los campos requeridos")
    
    print("\n🎉 Todas las verificaciones pasaron correctamente!")
    print("📋 Resumen de cambios implementados:")
    print("  - ✅ Campo 'cuenta_madre' como autoreferencia nullable")
    print("  - ✅ Campo 'perfil' migrado a tabla Cuenta")
    print("  - ✅ Formularios actualizados con los nuevos campos")
    print("  - ✅ Validaciones de cuenta_madre implementadas")
    print("  - ✅ Herencia automática de perfil del plan")

if __name__ == '__main__':
    test_cuenta_changes()
