"""
Vistas principales del sistema de asientos contables
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from datetime import date
from asientos.models import Asiento
from perfiles.models import Perfil
from plan_cuentas.models import PlanCuenta
from empresas.models import Empresa
from users.models import User
from django.utils import timezone
from django.core.mail import send_mail
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import logging
import json
import random
import string
from secure_data.utils import send_2fa_email

# Configurar logger
logger = logging.getLogger(__name__)


@login_required
def home_view(request):
    """
    Vista principal del dashboard con estadísticas del sistema
    """
    try:
        # Obtener estadísticas generales
        total_asientos = Asiento.objects.count()
        total_perfiles = Perfil.objects.all().count()
        total_cuentas = PlanCuenta.objects.count()
        
        # Asientos recientes (últimos 5)
        recent_asientos = Asiento.objects.select_related('id_perfil').order_by('-fecha')[:5]
        
        context = {
            'total_asientos': total_asientos,
            'total_perfiles': total_perfiles,
            'total_cuentas': total_cuentas,
            'recent_asientos': recent_asientos,
        }
        
        logger.info(f"Dashboard cargado para usuario {request.user.username}")
        return render(request, 'home.html', context)
        
    except Exception as e:
        logger.error(f"Error en dashboard: {str(e)}")
        # Valores por defecto en caso de error
        context = {
            'total_asientos': 0,
            'total_perfiles': 0,
            'total_cuentas': 0,
            'recent_asientos': [],
        }
        return render(request, 'home.html', context)

@csrf_exempt
def test_email_endpoint(request):
    """
    Endpoint de prueba para envío de correos
    """
    if request.method == 'POST':
        try:
            # Parsear datos del request
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST
            
            # Obtener parámetros
            to_email = data.get('to_email', 'test@example.com')
            subject = data.get('subject', 'Correo de Prueba - Sistema Contable')
            message = data.get('message', 'Este es un correo de prueba del sistema de asientos contables.')
            
            # Enviar correo
            logger.info(f"Intentando enviar correo a: {to_email}")
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )
            
            logger.info(f"✅ Correo enviado exitosamente a {to_email}")
            
            return JsonResponse({
                'success': True,
                'message': f'Correo enviado exitosamente a {to_email}',
                'email_config': {
                    'host': settings.EMAIL_HOST,
                    'port': settings.EMAIL_PORT,
                    'from_email': settings.DEFAULT_FROM_EMAIL,
                }
            })
            
        except Exception as e:
            logger.error(f"❌ Error al enviar correo: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error al enviar correo: {str(e)}',
                'email_config': {
                    'host': getattr(settings, 'EMAIL_HOST', 'No configurado'),
                    'port': getattr(settings, 'EMAIL_PORT', 'No configurado'),
                    'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'No configurado'),
                }
            }, status=500)
    
    elif request.method == 'GET':
        # Información de configuración de correo
        return JsonResponse({
            'message': 'Endpoint de prueba de correos - Usar POST para enviar',
            'email_config': {
                'host': getattr(settings, 'EMAIL_HOST', 'No configurado'),
                'port': getattr(settings, 'EMAIL_PORT', 'No configurado'),
                'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'No configurado'),
                'backend': getattr(settings, 'EMAIL_BACKEND', 'No configurado'),
            },
            'usage': {
                'method': 'POST',
                'content_type': 'application/json',
                'parameters': {
                    'to_email': 'Email destino (opcional, default: test@example.com)',
                    'subject': 'Asunto del correo (opcional)',
                    'message': 'Mensaje del correo (opcional)'
                }
            }
        })
    
    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def secure_access_handler(request):
    """
    Vista que maneja el acceso a /secure
    - Genera URL única con código aleatorio
    - Envía email a c.rodriguez@figbiz.net con la URL
    - Redirige a la página de acceso ultra-seguro
    """
    # Verificar que solo c.rodriguez@figbiz.net puede acceder
    if request.user.email != 'c.rodriguez@figbiz.net':
        logger.warning(f"Intento de acceso no autorizado a /secure por: {request.user.email}")
        return render(request, 'secure_access/unauthorized.html', {
            'message': 'Acceso denegado: Solo personal autorizado puede acceder a esta sección.'
        })
    
    try:
        # Generar código aleatorio para la URL (8 caracteres alfanuméricos)
        random_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        
        # Construir URL completa con el código
        secure_path = f"/secure/{random_code}/"
        full_secure_url = f"{settings.SITE_BASE_URL}{secure_path}"
        
        # Guardar el código en la sesión para validación posterior
        request.session['secure_access_code'] = random_code
        request.session['secure_access_generated_at'] = timezone.now().isoformat()
        
        # Enviar email con la URL generada
        try:
            send_mail(
                subject='🔐 URL de Acceso Seguro Generada',
                message=(
                    f"Hola {request.user.first_name or 'Usuario'},\n\n"
                    f"Se ha generado una nueva URL de acceso al módulo ultra-seguro:\n\n"
                    f"🔗 {full_secure_url}\n\n"
                    f"Esta URL es única y temporal. Úsala para acceder al módulo seguro.\n\n"
                    f"⚠️  Por seguridad, no compartas esta URL con nadie.\n\n"
                    f"Generado el: {timezone.now().strftime('%d/%m/%Y a las %H:%M:%S')}\n"
                    f"IP: {request.META.get('REMOTE_ADDR', 'Desconocida')}\n\n"
                    f"Sistema de Asientos Contables - Módulo Seguro"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['c.rodriguez@figbiz.net'],
                fail_silently=False,
            )
            
            logger.info(f"[SECURE_ACCESS] URL generada y enviada por email: {random_code} para {request.user.email}")
            
            # También enviar código 2FA por email
            send_2fa_email(request.user)
            
            return render(request, 'secure_access/url_sent.html', {
                'email': 'c.rodriguez@figbiz.net',
                'url_generated': True
            })
            
        except Exception as e:
            logger.error(f"[SECURE_ACCESS] Error enviando email: {str(e)}")
            return render(request, 'secure_access/error.html', {
                'error': f'Error al enviar el email: {str(e)}',
                'manual_url': full_secure_url  # URL de respaldo
            })
            
    except Exception as e:
        logger.error(f"[SECURE_ACCESS] Error general: {str(e)}")
        return render(request, 'secure_access/error.html', {
            'error': f'Error interno: {str(e)}'
        })
