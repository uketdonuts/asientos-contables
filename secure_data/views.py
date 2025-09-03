from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import PermissionDenied
import json
import logging
import hashlib
import random
import string
from django_otp import match_token
from django_otp.models import Device
from .models import SecureDataMatrix, SecureAccessLog, SecurePassword
from .forms import SecureAccessForm, SecureDataEditForm
from .utils import send_2fa_email, validate_email_2fa
from django.urls import reverse

logger = logging.getLogger(__name__)

User = get_user_model()

def get_active_passwords():
    """Obtiene las contraseñas activas desde la base de datos"""
    decoy_passwords = list(SecurePassword.objects.filter(
        password_type='decoy', 
        is_active=True
    ).values_list('password_text', flat=True))
    
    real_passwords = list(SecurePassword.objects.filter(
        password_type='real', 
        is_active=True
    ).values_list('password_text', flat=True))
    
    return decoy_passwords, real_passwords

def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@login_required
def secure_access_view(request):
    """Vista principal de acceso seguro - Solo para c.rodriguez@figbiz.net"""
    
    # Verificación estricta del usuario autorizado
    if request.user.email != 'c.rodriguez@figbiz.net':
        logger.warning(f"Intento de acceso no autorizado por: {request.user.email}")
        raise PermissionDenied("Acceso denegado: Usuario no autorizado")
    
    # Obtener el código de acceso desde la URL
    access_code = request.resolver_match.kwargs.get('access_code')
    
    # Validar que el código de acceso coincida con el almacenado en la sesión
    stored_code = request.session.get('secure_access_code')
    if not access_code or not stored_code or access_code != stored_code:
        logger.warning(f"Código de acceso inválido: {access_code} vs {stored_code}")
        raise PermissionDenied("Código de acceso inválido o expirado")
    
    # Si ya hay acceso seguro concedido, redirigir directamente a la matriz
    if request.session.get('secure_access_granted', False):
        return redirect('secure_data:matrix_view')
    
    if request.method == 'POST':
        form = SecureAccessForm(request.POST, user=request.user)
        if form.is_valid():
            password = form.cleaned_data['password']
            email_code = form.cleaned_data['verification_code']
            app_code = form.cleaned_data['app_verification_code']
            
            # Validar códigos 2FA
            if not validate_email_2fa(request.user, email_code):
                messages.error(request, "Código 2FA de email inválido")
                return render(request, 'secure_data/access.html', {'form': form})
            
            # Validar código de app authenticator
            if not match_token(request.user, app_code):
                messages.error(request, "Código 2FA de aplicación inválido")
                return render(request, 'secure_data/access.html', {'form': form})
            
            # Obtener contraseñas activas desde la base de datos
            decoy_passwords, real_passwords = get_active_passwords()
            
            # Verificar contraseña y determinar tipo
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            is_decoy = password in decoy_passwords
            is_real = password in real_passwords
            
            if not (is_decoy or is_real):
                messages.error(request, "Contraseña de acceso inválida")
                # Log intento fallido
                SecureAccessLog.objects.create(
                    user=request.user,
                    ip_address=get_client_ip(request),
                    password_type='unknown',
                    success=False,
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                return render(request, 'secure_data/access.html', {'form': form})
            
            # Acceso exitoso - guardar en sesión
            password_type = 'decoy' if is_decoy else 'real'
            request.session['secure_access_granted'] = True
            request.session['secure_password_hash'] = password_hash
            request.session['secure_password_type'] = password_type
            
            # Guardar timestamp para el middleware
            import time
            request.session['secure_access_time'] = time.time()
            
            # Log acceso exitoso
            SecureAccessLog.objects.create(
                user=request.user,
                ip_address=get_client_ip(request),
                password_type=password_type,
                success=True,
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f"Acceso concedido - Modo: {'Información Pública' if is_decoy else 'Información Confidencial'}")
            return redirect('secure_data:matrix_view')
    else:
        form = SecureAccessForm(user=request.user)
        # Enviar código 2FA por email
        send_2fa_email(request.user)
    
    return render(request, 'secure_data/access.html', {'form': form})

@login_required
def matrix_view(request):
    """Vista de matriz tipo Excel infinita para visualizar/editar datos"""
    
    # Verificar acceso autorizado
    if (not request.session.get('secure_access_granted') or 
        request.user.email != 'c.rodriguez@figbiz.net'):
        return redirect('secure_data:access')
    
    password_hash = request.session.get('secure_password_hash')
    password_type = request.session.get('secure_password_type')
    
    # Obtener rango de datos existentes para optimizar la carga inicial
    existing_data = SecureDataMatrix.objects.filter(password_hash=password_hash)
    
    max_row = 0
    max_col = 0
    
    if existing_data.exists():
        max_row = max(existing_data.values_list('row_index', flat=True))
        max_col = max(existing_data.values_list('col_index', flat=True))
    
    # Cargar al menos 50x26 celdas (como Excel inicial) o los datos existentes + buffer
    initial_rows = max(50, max_row + 10)
    initial_cols = max(26, max_col + 5)
    
    # Cargar datos existentes
    matrix_data = {}
    for data_obj in existing_data:
        if data_obj.row_index not in matrix_data:
            matrix_data[data_obj.row_index] = {}
        matrix_data[data_obj.row_index][data_obj.col_index] = data_obj.get_decrypted_value(password_hash)
    
    context = {
        'matrix_data': matrix_data,
        'password_type': password_type,
        'is_real_data': password_type == 'real',
        'initial_rows': initial_rows,
        'initial_cols': initial_cols,
        'max_row': max_row,
        'max_col': max_col
    }
    
    return render(request, 'secure_data/matrix_infinite.html', context)

@login_required
@csrf_exempt
def load_cells(request):
    """API para cargar celdas dinámicamente (scroll infinito)"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    # Verificar acceso autorizado
    if (not request.session.get('secure_access_granted') or 
        request.user.email != 'c.rodriguez@figbiz.net'):
        return JsonResponse({'success': False, 'error': 'Acceso no autorizado'})
    
    try:
        data = json.loads(request.body)
        start_row = int(data.get('start_row', 0))
        end_row = int(data.get('end_row', 50))
        start_col = int(data.get('start_col', 0))
        end_col = int(data.get('end_col', 26))
        
        password_hash = request.session.get('secure_password_hash')
        
        # Cargar datos del rango solicitado
        cells_data = {}
        existing_data = SecureDataMatrix.objects.filter(
            password_hash=password_hash,
            row_index__gte=start_row,
            row_index__lt=end_row,
            col_index__gte=start_col,
            col_index__lt=end_col
        )
        
        for data_obj in existing_data:
            row_key = str(data_obj.row_index)
            col_key = str(data_obj.col_index)
            
            if row_key not in cells_data:
                cells_data[row_key] = {}
            
            cells_data[row_key][col_key] = data_obj.get_decrypted_value(password_hash)
        
        return JsonResponse({
            'success': True,
            'cells': cells_data,
            'start_row': start_row,
            'end_row': end_row,
            'start_col': start_col,
            'end_col': end_col
        })
    
    except Exception as e:
        logger.error(f"Error loading cells: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Error interno del servidor'})

@login_required
@csrf_exempt
def update_cell(request):
    """API para actualizar una celda de la matriz"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    # Verificar acceso autorizado
    if (not request.session.get('secure_access_granted') or 
        request.user.email != 'c.rodriguez@figbiz.net'):
        return JsonResponse({'success': False, 'error': 'Acceso no autorizado'})
    
    try:
        data = json.loads(request.body)
        row = int(data.get('row'))
        col = int(data.get('col'))
        value = data.get('value', '')
        
        password_hash = request.session.get('secure_password_hash')
        password_type = request.session.get('secure_password_type')
        
        with transaction.atomic():
            # Obtener o crear el objeto
            data_obj, created = SecureDataMatrix.objects.get_or_create(
                password_hash=password_hash,
                row_index=row,
                col_index=col,
                defaults={
                    'data_type': password_type
                }
            )
            
            # Encriptar y guardar el nuevo valor
            data_obj.set_encrypted_value(value, password_hash)
            data_obj.save()
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        logger.error(f"Error updating cell: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Error interno del servidor'})

@login_required
@csrf_exempt
def logout_secure(request):
    """Cerrar sesión del módulo seguro y hacer logout completo del usuario"""
    from django.contrib.auth import logout
    
    # Aceptar tanto GET como POST (para navigator.sendBeacon)
    if request.method not in ['GET', 'POST']:
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    # Limpiar datos de sesión del módulo seguro
    request.session.pop('secure_access_granted', None)
    request.session.pop('secure_password_hash', None)
    request.session.pop('secure_password_type', None)
    request.session.pop('secure_access_time', None)
    
    # Limpiar también datos de 2FA para forzar re-autenticación completa
    request.session.pop('2fa_verified', None)
    
    # Log de salida segura
    logger.info(f"Usuario {request.user.email} cerró sesión desde módulo ultra-seguro")
    
    # Para solicitudes POST (beacon), devolver JSON
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'success': True, 'message': 'Sesión segura cerrada'})
    
    # Para solicitudes GET, hacer logout completo y redirigir
    logout(request)
    
    messages.info(request, "Sesión segura cerrada. Has sido desconectado completamente del sistema.")
    return redirect('users:login')

@login_required
@csrf_exempt
def save_matrix(request):
    """API para guardar toda la matriz desde X-Spreadsheet"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    if not request.session.get('secure_access_granted'):
        return JsonResponse({'success': False, 'error': 'Acceso no autorizado'})
    
    try:
        data = json.loads(request.body)
        matrix_data = data.get('matrix_data', {})
        
        password_hash = request.session.get('secure_password_hash')
        if not password_hash:
            return JsonResponse({'success': False, 'error': 'Sesión no válida'})
        
        # Guardar el estado actual en el historial
        history = request.session.get('matrix_history', [])
        current_index = request.session.get('matrix_history_index', -1)
        
        # Si estamos en medio del historial, eliminar los estados futuros
        if current_index < len(history) - 1:
            history = history[:current_index + 1]
        
        # Agregar el nuevo estado al historial
        history.append(matrix_data)
        
        # Mantener un límite de 50 estados en el historial para optimizar memoria
        if len(history) > 50:
            history = history[-50:]
        
        # Actualizar el historial en la sesión
        request.session['matrix_history'] = history
        request.session['matrix_history_index'] = len(history) - 1
        request.session.modified = True
        
        # Guardar los cambios en la base de datos
        cells_updated = 0
        
        # Verificar que matrix_data sea un diccionario
        if not isinstance(matrix_data, dict):
            return JsonResponse({
                'success': False,
                'error': f'Formato de datos inválido: se esperaba dict, se recibió {type(matrix_data).__name__}'
            })
        
        for row_idx, row_data in matrix_data.items():
            if not isinstance(row_data, dict):
                logger.warning(f"Fila {row_idx} no es un diccionario, saltando...")
                continue
                
            for col_idx, value in row_data.items():
                if value:  # Solo guardar celdas con contenido
                    data_obj, created = SecureDataMatrix.objects.get_or_create(
                        row_index=int(row_idx),
                        col_index=int(col_idx),
                        password_hash=password_hash,
                        defaults={
                            'data_type': request.session.get('secure_password_type', 'real')
                        }
                    )
                    data_obj.set_encrypted_value(value, password_hash)
                    data_obj.save()
                    cells_updated += 1
        
        return JsonResponse({
            'success': True,
            'cells_updated': cells_updated
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@csrf_exempt
def matrix_undo(request):
    """Vista para deshacer cambios en la matriz"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    if not request.session.get('secure_access_granted'):
        return JsonResponse({'success': False, 'error': 'Acceso no autorizado'})
    
    try:
        # Obtener el historial de cambios de la sesión
        history = request.session.get('matrix_history', [])
        current_index = request.session.get('matrix_history_index', -1)
        
        if not history or current_index <= 0:
            return JsonResponse({
                'success': False,
                'error': 'No hay más acciones para deshacer'
            })
        
        # Ir al estado anterior
        previous_index = current_index - 1
        previous_state = history[previous_index]
        
        # Actualizar la matriz con el estado anterior
        password_hash = request.session.get('secure_password_hash')
        
        # Limpiar todas las celdas existentes para este password_hash
        SecureDataMatrix.objects.filter(
            password_hash=password_hash
        ).delete()
        
        # Recrear las celdas con el estado anterior
        for row_idx, row_data in previous_state.items():
            for col_idx, value in row_data.items():
                if value:  # Solo crear celdas con contenido
                    data_obj = SecureDataMatrix(
                        row_index=int(row_idx),
                        col_index=int(col_idx),
                        password_hash=password_hash,
                        data_type=request.session.get('secure_password_type', 'real')
                    )
                    data_obj.set_encrypted_value(value, password_hash)
                    data_obj.save()
        
        # Actualizar el índice del historial
        request.session['matrix_history_index'] = previous_index
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'matrix_data': previous_state
        })
        
    except Exception as e:
        logger.error(f"Error en matrix_undo: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error al deshacer: {str(e)}'
        })

@login_required
@csrf_exempt
def matrix_redo(request):
    """Vista para rehacer cambios en la matriz"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    if not request.session.get('secure_access_granted'):
        return JsonResponse({'success': False, 'error': 'Acceso no autorizado'})
    
    try:
        # Obtener el historial de cambios de la sesión
        history = request.session.get('matrix_history', [])
        current_index = request.session.get('matrix_history_index', -1)
        
        if not history or current_index >= len(history) - 1:
            return JsonResponse({
                'success': False,
                'error': 'No hay acciones para rehacer'
            })
        
        # Ir al siguiente estado
        next_index = current_index + 1
        next_state = history[next_index]
        
        # Actualizar la matriz con el siguiente estado
        password_hash = request.session.get('secure_password_hash')
        
        # Limpiar todas las celdas existentes para este password_hash
        SecureDataMatrix.objects.filter(
            password_hash=password_hash
        ).delete()
        
        # Recrear las celdas con el siguiente estado
        for row_idx, row_data in next_state.items():
            for col_idx, value in row_data.items():
                if value:  # Solo crear celdas con contenido
                    data_obj = SecureDataMatrix(
                        row_index=int(row_idx),
                        col_index=int(col_idx),
                        password_hash=password_hash,
                        data_type=request.session.get('secure_password_type', 'real')
                    )
                    data_obj.set_encrypted_value(value, password_hash)
                    data_obj.save()
        
        # Actualizar el índice del historial
        request.session['matrix_history_index'] = next_index
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'matrix_data': next_state
        })
        
    except Exception as e:
        logger.error(f"Error en matrix_redo: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error al rehacer: {str(e)}'
        })

@login_required
@csrf_exempt
def matrix_save(request):
    """Vista para guardar cambios en la matriz"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    if not request.session.get('secure_access_granted'):
        return JsonResponse({'success': False, 'error': 'Acceso no autorizado'})
    
    try:
        data = json.loads(request.body)
        changes = data.get('changes', [])
        
        password_hash = request.session.get('secure_password_hash')
        if not password_hash:
            return JsonResponse({'success': False, 'error': 'Sesión no válida'})
        
        cells_updated = 0
        for change in changes:
            row = change.get('row')
            col = change.get('col')
            value = change.get('value')
            
            # Actualizar o crear el valor en la matriz
            data_obj, created = SecureDataMatrix.objects.get_or_create(
                row_index=row,
                col_index=col,
                password_hash=password_hash,
                defaults={
                    'data_type': request.session.get('secure_password_type', 'real')
                }
            )
            data_obj.set_encrypted_value(value, password_hash)
            data_obj.save()
            cells_updated += 1
        
        return JsonResponse({
            'success': True,
            'cells_updated': cells_updated
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        logger.error(f"Error en matrix_save: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

def matrix_exit(request):
    """Vista para salir de la matriz"""
    return redirect('home')
