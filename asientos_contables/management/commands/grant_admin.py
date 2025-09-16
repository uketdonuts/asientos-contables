from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Grant admin access to a user by email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email of the user')

    def handle(self, *args, **options):
        email = options['email']

        try:
            # Find user by email
            user = User.objects.get(email=email)
            self.stdout.write(f"Found user: {user.username} ({user.email})")

            # Update user permissions
            user.is_superuser = True
            user.is_staff = True
            user.role = 'admin'
            user.save()

            self.stdout.write(
                self.style.SUCCESS(f"✅ Successfully granted admin access to {user.username}")
            )
            self.stdout.write(f"   - is_superuser: {user.is_superuser}")
            self.stdout.write(f"   - is_staff: {user.is_staff}")
            self.stdout.write(f"   - role: {user.role}")

        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ User with email '{email}' not found")
            )
            self.stdout.write("Available users:")
            for user in User.objects.all():
                self.stdout.write(f"   - {user.username} ({user.email}) - role: {user.role}")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error: {e}")
            )