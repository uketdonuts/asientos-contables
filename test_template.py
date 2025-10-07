#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'asientos_contables.settings')
sys.path.append('/app')
django.setup()

from django.template import Template, Context

template = Template('{% url "asientos:get_cuentas_for_perfil" "dummy" %}')
context = Context({})
result = template.render(context)
print(f'Template result: {result}')
print(f'After replace dummy->1: {result.replace("dummy", "1")}')