from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('empresas', '0003_alter_empresa_id'),
        ('perfiles', '0007_alter_perfil_nombre'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlanCuenta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('grupo', models.CharField(max_length=50)),
                ('descripcion', models.CharField(max_length=200)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='empresas.empresa')),
                ('perfil', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='perfiles.perfil')),
            ],
            options={
                'verbose_name': 'Plan de Cuentas',
                'verbose_name_plural': 'Planes de Cuentas',
                'db_table': 'plan_cuentas_plancuenta',
                'ordering': ['grupo'],
            },
        ),
        migrations.CreateModel(
            name='Cuenta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cuenta', models.CharField(max_length=50)),
                ('descripcion', models.CharField(max_length=200)),
                ('plan_cuentas', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='plan_cuentas.plancuenta')),
            ],
            options={
                'verbose_name': 'Cuenta',
                'verbose_name_plural': 'Cuentas',
                'db_table': 'plan_cuentas_cuenta',
                'ordering': ['cuenta'],
            },
        ),
        migrations.AddConstraint(
            model_name='plancuenta',
            constraint=models.UniqueConstraint(fields=('empresa', 'grupo'), name='plan_cuentas_plancuenta_empresa_grupo_uniq'),
        ),
        migrations.AddConstraint(
            model_name='cuenta',
            constraint=models.UniqueConstraint(fields=('plan_cuentas', 'cuenta'), name='plan_cuentas_cuenta_plan_cuentas_cuenta_uniq'),
        ),
    ] 