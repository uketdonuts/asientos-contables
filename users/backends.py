from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Backend de autenticación personalizado que permite login con email o username
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        if username is None or password is None:
            return
        
        try:
            # Buscar usuario por username o email
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
            
            # Verificar la contraseña
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            # Ejecutar verificación de contraseña por defecto para evitar ataques de timing
            User().set_password(password)
            return None
        
        return None
    
    def user_can_authenticate(self, user):
        """
        Rechazar usuarios con is_active=False. Los backends personalizados pueden
        anular este método si tienen sus propias reglas de activación.
        """
        is_active = getattr(user, 'is_active', None)
        return is_active or is_active is None
