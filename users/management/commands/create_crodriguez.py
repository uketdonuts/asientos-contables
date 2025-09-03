import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Crea o actualiza el usuario especial c.rodriguez@figbiz.net"

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            dest="password",
            help="Contraseña a usar para el usuario (si no se pasa, se lee SEED_CRODRIGUEZ_PASSWORD o se usa un valor por defecto)",
        )
        parser.add_argument(
            "--force-reset",
            action="store_true",
            dest="force_reset",
            help="Si el usuario existe, forzar actualización de la contraseña y flags",
        )

    def handle(self, *args, **options):
        pwd = options.get("password") or os.getenv("SEED_CRODRIGUEZ_PASSWORD", "ChangeMe123!")
        force_reset = options.get("force_reset", False)

        username = "c.rodriguez"
        email = "c.rodriguez@figbiz.net"
        role = "admin"
        is_staff = True
        usr_2fa = True

        user = User.objects.filter(username=username).first()
        if user:
            changed = []
            if force_reset:
                user.set_password(pwd)
                changed.append("password")
            if getattr(user, "role", None) != role:
                try:
                    user.role = role
                    changed.append(f"role={role}")
                except Exception:
                    # Some custom user models might not have 'role'
                    pass
            if user.is_staff != is_staff:
                user.is_staff = is_staff
                changed.append(f"is_staff={is_staff}")
            if getattr(user, "usr_2fa", False) != usr_2fa:
                try:
                    user.usr_2fa = usr_2fa
                    changed.append(f"usr_2fa={usr_2fa}")
                except Exception:
                    pass

            if changed:
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Actualizado usuario '{username}' ({', '.join(changed)})"))
            else:
                self.stdout.write(f"Sin cambios para usuario '{username}'")
            return

        # Crear usuario si no existe
        user = User.objects.create_user(
            username=username,
            email=email,
            password=pwd,
            role=role if hasattr(User, 'role') or hasattr(user if 'user' in locals() else User, 'role') else None,
            usr_2fa=usr_2fa,
        )
        # Asegurar is_staff
        user.is_staff = is_staff
        try:
            user.save(update_fields=["is_staff"])
        except Exception:
            user.save()

        self.stdout.write(self.style.SUCCESS(f"Creado usuario '{username}' (email={email}, staff={is_staff}, 2FA={usr_2fa})"))
