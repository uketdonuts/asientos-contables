#!/bin/bash

# Script para actualizar la tolerancia de dispositivos TOTP existentes
# para mejorar la compatibilidad con apps de autenticación

echo "🔄 Actualizando tolerancia de dispositivos TOTP..."

python manage.py update_2fa_tolerance --tolerance=3

echo "✅ Actualización completada"