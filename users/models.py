from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from datetime import datetime
import json

class UserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('role', 'user')
        extra_fields.setdefault('usr_fecha_alta', None)
        extra_fields.setdefault('usr_fecha_baja', None)
        extra_fields.setdefault('usr_estado', True)
        
        if extra_fields['usr_fecha_alta'] is not None and isinstance(extra_fields['usr_fecha_alta'], datetime):
            extra_fields['usr_fecha_alta'] = extra_fields['usr_fecha_alta'].isoformat()
        if extra_fields['usr_fecha_baja'] is not None and isinstance(extra_fields['usr_fecha_baja'], datetime):
            extra_fields['usr_fecha_baja'] = extra_fields['usr_fecha_baja'].isoformat()
        
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        user = self.create_user(username, email, password, **extra_fields)
        user.role = 'admin'
        user.save(using=self._db)
        return user

class User(AbstractUser):
    usr_id = models.AutoField(primary_key=True)
    usr_fecha_alta = models.DateTimeField(null=True, blank=True)
    usr_fecha_baja = models.DateTimeField(null=True, blank=True)
    usr_estado = models.BooleanField(default=True)
    usr_2fa = models.BooleanField(default=False, verbose_name="Autenticación de dos factores")
    usr_recovery_codes = models.TextField(null=True, blank=True, help_text="Códigos de recuperación para 2FA")
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('supervisor', 'Supervisor'),
        ('user', 'User'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    
    objects = UserManager()
    
    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = 'admin'
            self.is_staff = True  # Los superusuarios siempre deben tener acceso al admin
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
        
    def get_recovery_codes(self):
        """Obtiene los códigos de recuperación como lista."""
        if not self.usr_recovery_codes:
            return []
        try:
            return json.loads(self.usr_recovery_codes)
        except json.JSONDecodeError:
            return []
            
    def set_recovery_codes(self, codes):
        """Guarda la lista de códigos de recuperación."""
        self.usr_recovery_codes = json.dumps(codes)
        self.save(update_fields=['usr_recovery_codes'])