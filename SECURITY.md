# Guía de Seguridad - Configuración de Producción

## ⚠️ IMPORTANTE: Archivos Sensibles

Los siguientes archivos contienen información sensible y **NUNCA** deben subirse a git:

- `docker.env` - Variables de entorno con contraseñas de producción
- `passwords.txt` - Archivo con contraseñas generadas
- `*.secret` - Cualquier archivo con extensión .secret
- `db.sqlite3` - Base de datos local con datos

## 🔐 Configuración Inicial para Producción

### 1. Crear archivo docker.env

```bash
# Copia el archivo de ejemplo
copy docker.env.example docker.env
```

### 2. Generar contraseñas seguras

Usa Python para generar contraseñas fuertes:

```bash
# Para DB_PASSWORD (32 caracteres)
python -c "import secrets; import string; chars = string.ascii_letters + string.digits + '!@#$%%^&*()-_=+'; print(''.join(secrets.choice(chars) for _ in range(32)))"

# Para MYSQL_ROOT_PASSWORD (32 caracteres)
python -c "import secrets; import string; chars = string.ascii_letters + string.digits + '!@#$%%^&*()-_=+'; print(''.join(secrets.choice(chars) for _ in range(32)))"

# Para SECRET_KEY (50 caracteres)
python -c "import secrets; import string; chars = string.ascii_letters + string.digits + '!@#$%%^&*()-_=+'; print(''.join(secrets.choice(chars) for _ in range(50)))"
```

### 3. Editar docker.env

Abre `docker.env` y reemplaza todos los valores `CHANGE_ME` con las contraseñas generadas.

### 4. Configurar para producción

Asegúrate de que estas variables estén configuradas correctamente:

```env
DEBUG=0
TWO_FACTOR_BYPASS=0
```

## 📝 Checklist de Seguridad

- [ ] `docker.env` creado con contraseñas únicas y fuertes
- [ ] DEBUG=0 en producción
- [ ] TWO_FACTOR_BYPASS=0 en producción
- [ ] Contraseñas guardadas en un gestor de contraseñas seguro
- [ ] `.gitignore` configurado correctamente
- [ ] `docker.env` NO está en el repositorio git
- [ ] `passwords.txt` NO está en el repositorio git

## 🔄 Si ya subiste archivos sensibles

Si accidentalmente subiste `docker.env` o `passwords.txt` al repositorio:

1. Cámbialas contraseñas INMEDIATAMENTE
2. Elimina el archivo del historial de git:
   ```bash
   git rm --cached docker.env
   git commit -m "Remove sensitive file from tracking"
   git push
   ```
3. Considera limpiar el historial completo si las contraseñas eran de producción

## 📚 Más información

- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [Docker Secrets](https://docs.docker.com/engine/swarm/secrets/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
