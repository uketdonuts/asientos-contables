#!/usr/bin/env python
import sqlite3

def main():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # Ver tablas disponibles
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('Tablas en la base de datos:')
    for table in tables:
        print(f'- {table[0]}')

    print('\n' + '='*50)

    # Buscar perfiles
    cursor.execute("SELECT id, nombre, descripcion FROM perfiles_perfil")
    perfiles = cursor.fetchall()
    print(f'Perfiles encontrados ({len(perfiles)}):')
    for perfil in perfiles:
        print(f'- ID: {perfil[0]}, Nombre: {perfil[1]}, Descripción: {perfil[2]}')

    # Buscar el perfil "compra activos"
    cursor.execute("SELECT id, nombre FROM perfiles_perfil WHERE nombre LIKE ?", ('%compra activos%',))
    perfil_compra = cursor.fetchone()

    if not perfil_compra:
        print("\nNo se encontró el perfil 'compra activos'")
        conn.close()
        return

    perfil_id, perfil_nombre = perfil_compra
    print(f"\nPerfil encontrado: {perfil_nombre} (ID: {perfil_id})")

    # Buscar configuraciones de cuentas para este perfil
    cursor.execute("""
        SELECT ppc.cuenta_id, pc.cuenta, pc.descripcion, ppc.polaridad
        FROM perfiles_perfilplancuenta ppc
        JOIN plan_cuentas_cuenta pc ON ppc.cuenta_id = pc.id
        WHERE ppc.perfil_id_id = ?
    """, (perfil_id,))

    configs = cursor.fetchall()
    print(f"\nCuentas relacionadas ({len(configs)}):")
    print("-" * 80)

    for config in configs:
        cuenta_id, cuenta_codigo, cuenta_desc, polaridad = config
        polaridad_desc = "Positiva (+ / Debe)" if polaridad == '+' else "Negativa (- / Haber)"
        print("2")

    conn.close()

if __name__ == '__main__':
    main()