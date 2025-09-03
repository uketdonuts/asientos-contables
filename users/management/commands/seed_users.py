import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Crea usuarios de ejemplo para todos los roles y el usuario especial c.rodriguez@figbiz.net. "
        "Usa variables de entorno para contraseñas si existen; si no, aplica valores por defecto."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force-reset",
            action="store_true",
            help="Si el usuario ya existe, forzar actualización de contraseña y flags (is_staff, role, 2FA)",
        )

    def handle(self, *args, **options):
        force_reset = options.get("force_reset", False)

        # Contraseñas configurables por entorno
        default_pwd = os.getenv("SEED_DEFAULT_PASSWORD", "ChangeMe123!")
        admin_pwd = os.getenv("SEED_ADMIN_PASSWORD", default_pwd)
        supervisor_pwd = os.getenv("SEED_SUPERVISOR_PASSWORD", default_pwd)
        user_pwd = os.getenv("SEED_USER_PASSWORD", default_pwd)
        crodriguez_pwd = os.getenv("SEED_CRODRIGUEZ_PASSWORD", default_pwd)

        created_or_updated = []

        # 1) Superusuario admin
        created_or_updated.append(
            self._ensure_superuser(
                username="admin",
                email="admin@example.com",
                password=admin_pwd,
                force_reset=force_reset,
            )
        )

        # 2) Supervisor (staff, no superuser)
        created_or_updated.append(
            self._ensure_user(
                username="supervisor",
                email="supervisor@example.com",
                role="supervisor",
                password=supervisor_pwd,
                is_staff=True,
                usr_2fa=True,
                force_reset=force_reset,
            )
        )

        # 3) Usuario normal
        created_or_updated.append(
            self._ensure_user(
                username="user",
                email="user@example.com",
                role="user",
                password=user_pwd,
                is_staff=False,
                usr_2fa=False,
                force_reset=force_reset,
            )
        )

        # 4) Usuario especial c.rodriguez
        created_or_updated.append(
            self._ensure_user(
                username="c.rodriguez",
                email="c.rodriguez@figbiz.net",
                role="admin",  # privilegios altos pero sin superusuario
                password=crodriguez_pwd,
                is_staff=True,
                usr_2fa=True,
                force_reset=force_reset,
            )
        )

        # Resumen
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Usuarios sembrados/actualizados:"))
        for msg in created_or_updated:
            self.stdout.write(f" - {msg}")
        self.stdout.write("")
        self.stdout.write("Credenciales por defecto (si no se pasaron por entorno):")
        self.stdout.write(f" - admin / {self._mask(admin_pwd)}")
        self.stdout.write(f" - supervisor / {self._mask(supervisor_pwd)}")
        self.stdout.write(f" - user / {self._mask(user_pwd)}")
        self.stdout.write(f" - c.rodriguez / {self._mask(crodriguez_pwd)}")
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("Cambie estas contraseñas en producción."))

    def _mask(self, s: str) -> str:
        if not s:
            return "(vacía)"
        if len(s) <= 4:
            return "*" * len(s)
        return s[:2] + "*" * (len(s) - 4) + s[-2:]

    def _ensure_superuser(self, username: str, email: str, password: str, force_reset: bool = False) -> str:
        user = User.objects.filter(username=username).first()
        if user:
            changed = []
            if force_reset:
                user.set_password(password)
                changed.append("password")
            if not user.is_staff:
                user.is_staff = True
                changed.append("is_staff=True")
            if not user.is_superuser:
                user.is_superuser = True
                changed.append("is_superuser=True")
            # role se forzará a 'admin' al guardar si es superuser (ver save)
            if changed:
                user.save()
                return f"Actualizado superuser '{username}' ({', '.join(changed)})"
            return f"Sin cambios para superuser '{username}'"

        # Crear si no existe
        User.objects.create_superuser(username=username, email=email, password=password)
        return f"Creado superuser '{username}'"

    def _ensure_user(
        self,
        username: str,
        email: str,
        role: str,
        password: str,
        is_staff: bool,
        usr_2fa: bool,
        force_reset: bool = False,
    ) -> str:
        user = User.objects.filter(username=username).first()
        if user:
            changed = []
            if force_reset:
                user.set_password(password)
                changed.append("password")
            if user.role != role:
                user.role = role
                changed.append(f"role={role}")
            if user.is_staff != is_staff:
                user.is_staff = is_staff
                changed.append(f"is_staff={is_staff}")
            if getattr(user, "usr_2fa", False) != usr_2fa:
                user.usr_2fa = usr_2fa
                changed.append(f"usr_2fa={usr_2fa}")
            if changed:
                user.save()
                return f"Actualizado usuario '{username}' ({', '.join(changed)})"
            return f"Sin cambios para usuario '{username}'"

        # Crear si no existe
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            usr_2fa=usr_2fa,
        )
        user.is_staff = is_staff
        user.save(update_fields=["is_staff"])
        return f"Creado usuario '{username}' (role={role}, staff={is_staff}, 2FA={usr_2fa})"
