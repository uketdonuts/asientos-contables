#!/usr/bin/env python
import os
import sys
import django

# Configurar Django para el contenedor Docker
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asientos_contables.settings')
sys.path.append('/app')
django.setup()

from perfiles.models import Perfil, PerfilPlanCuenta
from plan_cuentas.models import Cuenta

def main():
    # Buscar el perfil "compra activos"
    perfil = Perfil.objects.filter(nombre__icontains='compra activos').first()

    if not perfil:
        print("No se encontró el perfil 'compra activos'")
        print("\nPerfiles disponibles:")
        perfiles = Perfil.objects.all()
        for p in perfiles:
            print(f"- {p.nombre}")
        return

    print(f"Perfil encontrado: {perfil.nombre}")
    print(f"Descripción: {perfil.descripcion or 'Sin descripción'}")
    print()

    # Obtener las configuraciones de cuentas para este perfil
    configs = PerfilPlanCuenta.objects.filter(perfil_id=perfil).select_related('cuentas_id').order_by('cuentas_id__cuenta')

    print(f"Cuentas relacionadas ({configs.count()}):")
    print("-" * 90)
    print(f"{'Código':<15} {'Descripción':<50} {'Polaridad'}")
    print("-" * 90)

    for config in configs:
        cuenta = config.cuentas_id
        polaridad = config.get_polaridad_display()
        print(f"{cuenta.cuenta:<15} {cuenta.descripcion:<50} {polaridad}")

if __name__ == '__main__':
    main()