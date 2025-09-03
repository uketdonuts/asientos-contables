from django.db import migrations, models
import django.db.models.deletion


def set_cuenta_perfil_from_plan(apps, schema_editor):
    Cuenta = apps.get_model('plan_cuentas', 'Cuenta')
    for cuenta in Cuenta.objects.all().iterator():
        if getattr(cuenta, 'perfil_id', None) is None and getattr(cuenta, 'plan_cuentas_id', None):
            plan = getattr(cuenta, 'plan_cuentas', None)
            if plan and getattr(plan, 'perfil_id', None):
                cuenta.perfil_id = plan.perfil_id
                cuenta.save(update_fields=['perfil_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('perfiles', '0008_perfilplancuenta'),
        ('plan_cuentas', '0002_alter_cuenta_options_alter_plancuenta_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cuenta',
            name='perfil',
            field=models.ForeignKey(blank=True, db_column='perfil_id', help_text='Perfil contable asociado', null=True, on_delete=django.db.models.deletion.CASCADE, to='perfiles.perfil', verbose_name='Perfil'),
        ),
        migrations.RunPython(set_cuenta_perfil_from_plan, migrations.RunPython.noop),
    ]
