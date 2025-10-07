#!/bin/sh

# Docker entrypoint script para Asientos Contables
set -e

# Función para esperar a que la base de datos esté disponible
wait_for_db() {
    echo "Esperando a que la base de datos esté disponible..."
    while ! nc -z "$DB_HOST" "$DB_PORT"; do
        echo "Base de datos no disponible, esperando..."
        sleep 2
    done
    echo "Base de datos disponible!"
}

# Main execution
main() {
    echo "Iniciando Asientos Contables..."
    echo "$(date)"
    
    # Sincronizar tiempo con NTP para evitar problemas con 2FA
    echo "Sincronizando tiempo con NTP..."
    timedatectl set-ntp true 2>/dev/null || true
    ntpdate pool.ntp.org 2>/dev/null || true
    echo "Tiempo sincronizado: $(date)"
    
    # Esperar a la base de datos si está configurada
    if [ "$DB_HOST" ] && [ "$DB_PORT" ]; then
        wait_for_db
    fi
    
    # Crear migraciones si no existen
    echo "Creando migraciones..."
    python manage.py makemigrations --noinput || true
    
    # Ejecutar migraciones básicas
    echo "Aplicando migraciones..."
    python manage.py migrate --noinput || true
    
    # Ejecutar el comando pasado como argumentos o runserver por defecto
    if [ "$#" -eq 0 ]; then
        exec python manage.py runserver 0.0.0.0:8000
    else
        exec "$@"
    fi
}

# Ejecutar función principal
main "$@"
