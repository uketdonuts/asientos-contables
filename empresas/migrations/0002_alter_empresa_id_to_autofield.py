# Generated manually for empresa ID change
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0001_initial'),
    ]

    operations = [
        # Paso 1: Crear nueva tabla con AutoField
        migrations.RunSQL(
            """
            CREATE TABLE empresas_empresa_new (
                id INT AUTO_INCREMENT PRIMARY KEY,
                type VARCHAR(50),
                nombre VARCHAR(200) NOT NULL,
                descripcion LONGTEXT,
                activa TINYINT(1) NOT NULL DEFAULT 1,
                fecha_creacion DATETIME(6) NOT NULL,
                fecha_modificacion DATETIME(6) NOT NULL
            );
            """,
            reverse_sql="""
            DROP TABLE IF EXISTS empresas_empresa_new;
            """
        ),
        
        # Paso 2: Insertar datos existentes
        migrations.RunSQL(
            """
            INSERT INTO empresas_empresa_new (type, nombre, descripcion, activa, fecha_creacion, fecha_modificacion)
            SELECT type, nombre, descripcion, activa, fecha_creacion, fecha_modificacion 
            FROM empresas_empresa 
            ORDER BY fecha_creacion;
            """,
            reverse_sql=""
        ),
        
        # Paso 3: Eliminar tabla antigua y renombrar la nueva
        migrations.RunSQL(
            """
            DROP TABLE empresas_empresa;
            RENAME TABLE empresas_empresa_new TO empresas_empresa;
            """,
            reverse_sql="""
            RENAME TABLE empresas_empresa TO empresas_empresa_new;
            CREATE TABLE empresas_empresa (
                id VARCHAR(24) PRIMARY KEY,
                type VARCHAR(50),
                nombre VARCHAR(200) NOT NULL,
                descripcion LONGTEXT,
                activa TINYINT(1) NOT NULL DEFAULT 1,
                fecha_creacion DATETIME(6) NOT NULL,
                fecha_modificacion DATETIME(6) NOT NULL
            );
            """
        ),
    ] 