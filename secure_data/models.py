from django.db import models
from django.contrib.auth import get_user_model
from cryptography.fernet import Fernet
from django.conf import settings
import base64
import hashlib
import json

User = get_user_model()

class SecureDataMatrix(models.Model):
    """
    Modelo para almacenar data ultra-secreta con encriptación AES-256
    """
    id = models.CharField(primary_key=True, max_length=64, editable=False)
    password_hash = models.CharField(max_length=128)  # Removed unique=True - will use unique_together instead
    data_type = models.CharField(max_length=20, choices=[
        ('decoy', 'Información Falsa'),
        ('real', 'Información Real')
    ])
    row_index = models.BigIntegerField()  # Soporte para índices grandes (infinito)
    col_index = models.BigIntegerField()  # Soporte para índices grandes (infinito)
    encrypted_value = models.TextField()  # Valor encriptado
    encryption_salt = models.CharField(max_length=64)  # Salt único por registro
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Dato Seguro"
        verbose_name_plural = "Datos Seguros"
        unique_together = ('password_hash', 'row_index', 'col_index')
        ordering = ['password_hash', 'row_index', 'col_index']
    
    def save(self, *args, **kwargs):
        if not self.id:
            unique_str = f"{self.password_hash}-{self.row_index}-{self.col_index}"
            self.id = hashlib.sha256(unique_str.encode()).hexdigest()
        super().save(*args, **kwargs)
    
    @staticmethod
    def encrypt_data(data, password_hash):
        """Encripta data usando AES-256 con salt único"""
        import os
        salt = base64.urlsafe_b64encode(os.urandom(32)).decode()
        
        # Crear clave derivada usando PBKDF2
        key_material = hashlib.pbkdf2_hmac(
            'sha256',
            password_hash.encode(),
            salt.encode(),
            100000  # 100k iteraciones
        )
        key = base64.urlsafe_b64encode(key_material[:32])
        
        # Encriptar con Fernet (AES-256)
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(json.dumps(data).encode())
        
        return base64.urlsafe_b64encode(encrypted_data).decode(), salt
    
    @staticmethod
    def decrypt_data(encrypted_data, salt, password_hash):
        """Desencripta data usando la misma clave derivada"""
        try:
            # Recrear la clave
            key_material = hashlib.pbkdf2_hmac(
                'sha256',
                password_hash.encode(),
                salt.encode(),
                100000
            )
            key = base64.urlsafe_b64encode(key_material[:32])
            
            # Desencriptar
            fernet = Fernet(key)
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(encrypted_bytes)
            
            return json.loads(decrypted_data.decode())
        except Exception:
            return None
    
    def get_decrypted_value(self, password_hash):
        """Obtiene el valor desencriptado"""
        return self.decrypt_data(self.encrypted_value, self.encryption_salt, password_hash)
    
    def set_encrypted_value(self, value, password_hash):
        """Establece un valor encriptado"""
        encrypted_value, salt = self.encrypt_data(value, password_hash)
        self.encrypted_value = encrypted_value
        self.encryption_salt = salt

class SecureAccessLog(models.Model):
    """Log de accesos al módulo seguro"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    password_type = models.CharField(max_length=20, choices=[
        ('decoy', 'Contraseña Falsa'),
        ('real', 'Contraseña Real')
    ])
    success = models.BooleanField(default=False)
    user_agent = models.TextField()
    
    class Meta:
        verbose_name = "Log de Acceso Seguro"
        verbose_name_plural = "Logs de Acceso Seguro"
        ordering = ['-access_time']

class SecurePassword(models.Model):
    """
    Modelo para gestionar las contraseñas secretas del módulo
    Estas contraseñas son independientes de las contraseñas de usuario
    """
    id = models.CharField(primary_key=True, max_length=64, editable=False)
    password_text = models.CharField(max_length=100, unique=True, verbose_name="Contraseña Secreta")
    password_hash = models.CharField(max_length=128, unique=True, verbose_name="Hash de la Contraseña")
    password_type = models.CharField(max_length=20, choices=[
        ('decoy', 'Información Falsa/Pública'),
        ('real', 'Información Real/Confidencial')
    ], verbose_name="Tipo de Información")
    description = models.CharField(max_length=200, blank=True, null=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Contraseña Secreta"
        verbose_name_plural = "Contraseñas Secretas"
        ordering = ['password_type', 'password_text']
    
    def save(self, *args, **kwargs):
        if not self.id:
            # Generar ID único basado en el texto de la contraseña
            unique_str = f"secure_password_{self.password_text}"
            self.id = hashlib.sha256(unique_str.encode()).hexdigest()
        
        # Generar hash de la contraseña automáticamente
        if self.password_text and not self.password_hash:
            self.password_hash = hashlib.sha256(self.password_text.encode()).hexdigest()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.password_text} ({self.get_password_type_display()})"
    
    @classmethod
    def get_active_passwords(cls, password_type=None):
        """Obtiene las contraseñas activas, opcionalmente filtradas por tipo"""
        queryset = cls.objects.filter(is_active=True)
        if password_type:
            queryset = queryset.filter(password_type=password_type)
        return queryset
