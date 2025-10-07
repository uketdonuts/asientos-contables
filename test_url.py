#!/usr/bin/env python
import urllib.request
import json

try:
    with urllib.request.urlopen('http://localhost:8000/asientos/perfil/1/cuentas/') as response:
        data = response.read().decode('utf-8')
        print(f'Status: {response.status}')
        print(f'Content: {data}')
        # Intentar parsear como JSON
        try:
            json_data = json.loads(data)
            print(f'JSON parsed successfully: {json_data}')
        except json.JSONDecodeError as e:
            print(f'Not valid JSON: {e}')
except Exception as e:
    print(f'Error: {e}')