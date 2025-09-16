from pathlib import Path
import os
import dj_database_url

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)  # Cargar y sobrescribir variables existentes
except ImportError:
    # Si dotenv no está disponible, continuar sin él
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'your-secret-key'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'testserver']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',
    'empresas',  # Nueva app para gestión de empresas
    'asientos',
    'asientos_detalle',
    'perfiles',
    'plan_cuentas',
    'django_otp',
    'django_otp.plugins.otp_totp',  # Para generar tokens TOTP (como Google Authenticator)
    'two_factor_auth',
    'secure_data',  # Módulo ultra-seguro
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'two_factor_auth.middleware.TwoFactorMiddleware',
    'secure_data.middleware.SecureSessionMiddleware',  # Middleware del módulo seguro
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'asientos_contables.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'asientos_contables.wsgi.application'

# Configuración de la base de datos para desarrollo local
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL')
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,  
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'es'  # cambiar a 'es' para español

TIME_ZONE = 'America/Bogota'

USE_I18N = True  # asegurarse de que esté habilitado

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Static files (CSS, JavaScript, Images) for production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'users:login'

AUTH_USER_MODEL = 'users.User'

# Backends de autenticación personalizados
AUTHENTICATION_BACKENDS = [
    'users.backends.EmailOrUsernameModelBackend',  # Login por email o username
    'django.contrib.auth.backends.ModelBackend',    # Backend por defecto
]

TWO_FACTOR_SMS_GATEWAY = 'two_factor.gateways.twilio.gateway.Twilio'
TWILIO_ACCOUNT_SID = 'tu_account_sid'
TWILIO_AUTH_TOKEN = 'tu_auth_token'
TWILIO_CALLER_ID = '+1234567890'

# Configuración de correo electrónico
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Configuración de django-otp para 2FA con tolerancia reducida
OTP_TOTP_TOLERANCE = 1  # Permitir solo 1 token antes/después (total ~90 segundos)
OTP_TOTP_ISSUER = 'Asientos Contables'  # Nombre que aparece en la app

# Para desarrollo local con MailHog
if os.getenv('DEBUG', 'False').lower() == '1' or os.getenv('DEBUG', 'False').lower() == 'true':
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'mailhog')  # Usar variable de entorno o 'mailhog' por defecto
    EMAIL_PORT = 1025
    EMAIL_USE_TLS = False
    EMAIL_USE_SSL = False
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''
else:
    # Para producción
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'email-smtp.us-east-1.amazonaws.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Sistema Contable <noreply@asientos-contables.local>')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Base URL del sitio para construir enlaces absolutos en emails
# Ajusta mediante variable de entorno SITE_BASE_URL en despliegues
SITE_BASE_URL = os.getenv('SITE_BASE_URL', 'http://localhost:8002')

# Temporary 2FA bypass flag (for troubleshooting)
TWO_FACTOR_BYPASS = os.getenv('TWO_FACTOR_BYPASS', '0').lower() in ('1', 'true', 'yes')

# Cache configuration for 2FA codes
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 120,  # 2 minutos (para coincidir con OTP por correo)
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Logging configuration for security module
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'secure': {
            'format': '[SECURITY] {asctime} - {levelname} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
        'secure_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'security.log'),
            'formatter': 'secure',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'secure_data': {
            'handlers': ['secure_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'perfiles': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)