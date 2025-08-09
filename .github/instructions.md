# Asientos Contables - Copilot Instructions

## Contexto del Proyecto

Este es un sistema de gestión de asientos contables desarrollado en Django con las siguientes características principales:

- **Framework**: Django 4.2
- **Base de Datos**: MySQL
- **Autenticación**: Autenticación de dos factores (2FA) obligatoria
- **Frontend**: Bootstrap para UI moderna y responsiva
- **Idioma**: Español (configuración regional Colombia)
- **Arquitectura**: Monolítica con apps modulares

## Estructura de Apps Django

### Apps Principales
- `asientos`: Gestión de asientos contables principales
- `asientos_detalle`: Detalles de cada asiento contable
- `perfiles`: Perfiles contables y configuraciones
- `plan_cuentas`: Plan de cuentas contables
- `users`: Gestión de usuarios con roles
- `two_factor_auth`: Autenticación de dos factores

### Modelos Clave
- `Asiento`: Registro principal de asiento contable
- `AsientoDetalle`: Detalles individuales de cada asiento
- `Perfil`: Perfil contable asociado a configuraciones
- `PlanCuenta`: Cuentas del plan contable
- `PerfilPlanCuenta`: Relación entre perfiles y cuentas
- `User`: Usuario personalizado con roles y 2FA

## Reglas de Programación CRÍTICAS

### 1. Balance Contable OBLIGATORIO
- **NUNCA** permitir que un asiento contable tenga un balance distinto de CERO
- La suma de débitos debe ser igual a la suma de créditos
- Validar siempre: `sum(polaridad '+') == sum(polaridad '-')`
- Implementar validación tanto en formularios como en modelos

### 2. Arquitectura de Datos
- Usar transacciones atómicas para operaciones críticas
- Mantener integridad referencial siempre
- Los IDs se generan con SHA256 basado en empresa-fecha o empresa-secuencial
- Empresa es campo obligatorio y predeterminado "DEFAULT"

### 3. Validaciones de Negocio
- Polaridad: '+' para DEBE, '-' para HABER
- PerfilPlanCuenta define la polaridad de cada cuenta en cada perfil
- AsientoDetalle debe tener perfil, cuenta, tipo_cuenta y valor obligatorios
- Validar que las cuentas pertenezcan a la empresa correcta

### 4. Manejo de Errores
- Usar ValidationError para errores de negocio
- Logging detallado para debugging (usar logger configurado)
- Respuestas JSON estructuradas para AJAX
- Manejo de excepciones en transacciones

### 5. Frontend y UX
- Bootstrap para todos los componentes UI
- Select2 para campos de selección complejos
- Validación JavaScript + validación servidor
- Mensajes informativos claros en español
- Formularios modales para operaciones rápidas

### 6. Seguridad
- Login obligatorio en todas las vistas
- 2FA obligatorio para todos los usuarios
- Validación CSRF en todos los formularios
- Roles de usuario: admin, supervisor, user

### 7. Patrones de Código
- Usar Class-Based Views cuando sea apropiado
- Function-Based Views para lógica compleja
- Formsets para relaciones maestro-detalle
- Serialización JSON para comunicación AJAX
- Usar select_related y prefetch_related para optimizar queries

### 8. Convenciones de Nomenclatura
- Campos en español para el dominio de negocio
- Métodos y variables en inglés/español mixto
- Nombres descriptivos para funciones
- Comentarios en español para lógica de negocio

## Flujo de Desarrollo

### Creación de Asientos
1. Crear asiento principal (Asiento)
2. Agregar detalles (AsientoDetalle) con validación de balance
3. Verificar que suma de polaridades sea cero
4. Confirmar transacción atómica

### Edición de Asientos
1. Cargar asiento existente con detalles
2. Permitir modificar detalles manteniendo balance
3. Re-validar balance antes de guardar
4. Actualizar en transacción atómica

### Validaciones en Cascada
1. Validar datos de entrada en formularios
2. Validar lógica de negocio en modelos
3. Validar integridad en base de datos
4. Confirmar balance final

## Tecnologías y Dependencias

### Backend
- Django 4.2 con ORM
- django-otp para 2FA
- dj-database-url para configuración DB
- mysqlclient para MySQL

### Frontend
- Bootstrap 4/5 para UI
- Select2 para campos avanzados
- JavaScript vanilla para interactividad
- HTMX opcional para funcionalidad dinámica

### Desarrollo
- python-dotenv para variables de entorno
- django-extensions para utilidades de desarrollo
- Logging configurado para debugging

## Comandos Útiles

### Desarrollo
```bash
python manage.py runserver
python manage.py migrate
python manage.py makemigrations
python manage.py collectstatic
```

### Docker
```bash
docker-compose up -d
docker-compose logs -f
- Asume que la aplicación siempre está corriendo en Docker
```

## Estándares de Calidad

### Testing
- Tests unitarios para validaciones críticas
- Tests de integración para flujos completos
- Tests de balance contable obligatorios

### Performance
- Optimizar queries con select_related
- Usar índices en campos de búsqueda frecuente
- Cachear datos estáticos cuando sea posible

### Mantenibilidad
- Código autodocumentado
- Funciones pequeñas y específicas
- Separación clara de responsabilidades
- Documentación actualizada

## Notas Importantes

- El balance contable es la regla MÁS IMPORTANTE del sistema
- Siempre usar transacciones para operaciones multi-modelo
- Los perfiles determinan las cuentas disponibles y sus polaridades
- La empresa es el contexto principal para todos los datos
- El sistema debe funcionar perfectamente sin JavaScript (progressive enhancement)

## Debugging

- Usar `logger.debug()` para seguimiento detallado
- Validar balance en múltiples puntos del flujo
- Verificar empresas y perfiles en cada operación
- Comprobar relaciones FK antes de guardar
