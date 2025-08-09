-- Configuración inicial de MySQL para Asientos Contables
-- Este script se ejecuta automáticamente al inicializar el contenedor

-- Configurar timezone
SET GLOBAL time_zone = '-05:00';

-- Configuraciones de seguridad
SET GLOBAL sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO';

-- Configurar charset para soporte completo de Unicode (incluyendo emojis)
SET GLOBAL character_set_server = 'utf8mb4';
SET GLOBAL collation_server = 'utf8mb4_unicode_ci';

-- Configuraciones de rendimiento
-- SET GLOBAL innodb_buffer_pool_size = 134217728; -- 128MB en bytes
SET GLOBAL max_connections = 200;

-- Configuraciones de logging para seguridad
SET GLOBAL log_bin_trust_function_creators = 1;
SET GLOBAL general_log = 'OFF';
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;

-- Crear base de datos si no existe
CREATE DATABASE IF NOT EXISTS asientos_contables;

-- Crear usuario y dar permisos
CREATE USER IF NOT EXISTS 'asientos_user'@'%' IDENTIFIED BY 'asientos_pass123';
GRANT ALL PRIVILEGES ON asientos_contables.* TO 'asientos_user'@'%';
GRANT ALL PRIVILEGES ON `test_asientos_contables`.* TO 'asientos_user'@'%';
GRANT ALL PRIVILEGES ON `test\_%`.* TO 'asientos_user'@'%';
FLUSH PRIVILEGES;

-- Mensaje de confirmación
SELECT 'MySQL inicializado correctamente para Asientos Contables' AS message;
