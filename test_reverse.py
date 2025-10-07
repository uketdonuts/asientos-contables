#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asientos_contables.settings')
sys.path.append('/app')
django.setup()

from django.urls import reverse

try:
    url = reverse('asientos:get_cuentas_for_perfil', kwargs={'perfil_id': '1'})
    print(f'URL generada: {url}')
except Exception as e:
    print(f'Error generando URL: {e}')