from django.db import migrations
from django.utils import timezone
from datetime import timedelta

def set_transition_period_for_existing_users(apps, schema_editor):
    """
    Este método marca a los usuarios existentes como en período de transición,
    guardando la fecha límite en la sesión cuando inicien sesión.
    """
    User = apps.get_model('users', 'User')
    for user in User.objects.all():
        # En lugar de activar usr_2fa directamente para usuarios existentes
        # lo dejaremos en False para que sean redirigidos a la configuración
        user.usr_2fa = False  
        user.save()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_usr_2fa'),
    ]

    operations = [
        migrations.RunPython(set_transition_period_for_existing_users),
    ]