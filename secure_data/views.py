from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
import json
import logging
import hashlib
import random
import string
from django_otp import match_token
from .models import SecureDataMatrix, SecureAccessLog, SecurePassword
from .forms import SecureAccessForm
from .utils import send_2fa_email, validate_email_2fa

logger = logging.getLogger(__name__)
User = get_user_model()

def get_active_passwords():
    """Obtiene las contraseñas activas desde la base de datos"""
    try:
        decoy_passwords = list(SecurePassword.objects.filter(
            password_type='decoy', 
            is_active=True
        ).values_list('password_text', flat=True))
        
        real_passwords = list(SecurePassword.objects.filter(
            password_type='real', 
            is_active=True
        ).values_list('password_text', flat=True))
        
        return decoy_passwords, real_passwords
    except Exception as e:
        logger.error(f"Error obteniendo contraseñas: {e}")
        return [], []

def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def validate_access_code(access_code):
    """Valida si el código de acceso es válido"""
    if len(access_code) == 12 and access_code.isalnum():
        return True
    return False

def validate_user_access(user):
    """Valida si el usuario tiene acceso al sistema seguro"""
    if not user.is_authenticated:
        return False
    
    # Lista de usuarios autorizados
    authorized_emails = ['c.rodriguez@figbiz.net']
    return user.email in authorized_emails

@login_required
def secure_access_view(request, access_code):
    """Vista principal para acceso a datos seguros con autenticación completa 2FA"""
    
    # Validar usuario autorizado
    if not validate_user_access(request.user):
        raise PermissionDenied("Acceso denegado: Usuario no autorizado")
    
    # Validar código de acceso
    if not validate_access_code(access_code):
        raise PermissionDenied("Código de acceso inválido o expirado")
    
    if request.method == 'POST':
        try:
            form = SecureAccessForm(request.POST, user=request.user)
            if form.is_valid():
                password = form.cleaned_data['password']
                email_code = form.cleaned_data.get('email_2fa_code')
                app_code = form.cleaned_data.get('app_2fa_code')
                
                logger.info(f"Intento de acceso para usuario {request.user.email}")
                
                # Validar código 2FA de email
                if not validate_email_2fa(request.user, email_code):
                    messages.error(request, "Código 2FA de email inválido")
                    return render(request, 'secure_data/access_form.html', {
                        'form': form, 
                        'access_code': access_code
                    })
                
                # Validar código 2FA de aplicación (opcional por ahora)
                if app_code:
                    try:
                        if not match_token(request.user, app_code):
                            messages.error(request, "Código 2FA de aplicación inválido")
                            return render(request, 'secure_data/access_form.html', {
                                'form': form, 
                                'access_code': access_code
                            })
                    except Exception as e:
                        logger.warning(f"Error validando app 2FA: {e}")
                        # Continuar sin validación de app si hay error
                
                # Obtener contraseñas activas
                decoy_passwords, real_passwords = get_active_passwords()
                all_passwords = decoy_passwords + real_passwords
                
                # Verificar contraseña
                if password not in all_passwords:
                    # Contraseña no válida - registrar intento
                    messages.error(request, "Contraseña de acceso inválida")
                    
                    try:
                        SecureAccessLog.objects.create(
                            user=request.user,
                            access_code=access_code,
                            success=False,
                            ip_address=get_client_ip(request),
                            user_agent=request.META.get('HTTP_USER_AGENT', ''),
                            is_decoy_attempt=True
                        )
                    except Exception as e:
                        logger.error(f"Error registrando log de acceso: {e}")
                    
                    return render(request, 'secure_data/access_form.html', {
                        'form': form, 
                        'access_code': access_code
                    })
                
                # Contraseña válida - determinar si es señuelo o real
                is_decoy = password in decoy_passwords
                
                # Registrar acceso exitoso
                try:
                    SecureAccessLog.objects.create(
                        user=request.user,
                        access_code=access_code, 
                        success=True,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        is_decoy_attempt=is_decoy
                    )
                except Exception as e:
                    logger.error(f"Error registrando log de acceso exitoso: {e}")
                
                # Guardar información de la sesión
                request.session['secure_password_used'] = password
                request.session['is_decoy_mode'] = is_decoy
                request.session['access_code'] = access_code
                
                mode_text = 'Información Pública' if is_decoy else 'Información Confidencial'
                messages.success(request, f"Acceso concedido - Modo: {mode_text}")
                
                return redirect('secure_data:matrix', access_code=access_code)
                
        except Exception as e:
            logger.error(f"Error en secure_access_view: {e}")
            messages.error(request, "Error interno del sistema")
    
    else:
        # GET request - mostrar formulario y enviar código 2FA por email (solo una vez por sesión)
        try:
            form = SecureAccessForm(user=request.user)
            
            # Verificar si ya se envió un código para este access_code en esta sesión
            session_key = f'2fa_sent_{access_code}'
            if not request.session.get(session_key):
                # Enviar código 2FA por email solo si no se ha enviado antes
                send_2fa_email(request.user)
                request.session[session_key] = True
                messages.info(request, "Se ha enviado un código 2FA a su email")
            else:
                messages.info(request, "Use el código 2FA enviado anteriormente a su email")
                
        except Exception as e:
            logger.error(f"Error enviando 2FA email: {e}")
            form = SecureAccessForm(user=request.user)
            messages.warning(request, "Error enviando código 2FA por email")
    
    return render(request, 'secure_data/access_form.html', {
        'form': form,
        'access_code': access_code
    })

@login_required  
def matrix_view(request, access_code):
    """Vista de matriz tipo Excel infinita para visualizar/editar datos"""
    
    # Validar usuario autorizado
    if not validate_user_access(request.user):
        raise PermissionDenied("Acceso denegado: Usuario no autorizado")
    
    # Validar código de acceso
    if not validate_access_code(access_code):
        raise PermissionDenied("Código de acceso inválido o expirado")
    
    # Verificar que el usuario haya pasado por el proceso de autenticación
    if not request.session.get('secure_password_used'):
        messages.error(request, "Debe autenticarse primero")
        return redirect('secure_data:access', access_code=access_code)
    
    # Obtener información de la sesión
    is_decoy_mode = request.session.get('is_decoy_mode', False)
    password_used = request.session.get('secure_password_used')
    password_hash = hashlib.sha256(password_used.encode()).hexdigest()
    password_type = 'decoy' if is_decoy_mode else 'real'
    
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
        'max_col': max_col,
        'access_code': access_code
    }
    
    return render(request, 'secure_data/matrix_infinite.html', context)

@login_required
def logout_secure(request, access_code):
    """Vista para cerrar sesión segura"""
    
    # Limpiar datos de sesión relacionados con acceso seguro
    session_keys_to_clear = [
        'secure_password_used',
        'is_decoy_mode', 
        'access_code',
        f'2fa_sent_{access_code}'  # Limpiar flag de código enviado
    ]
    
    for key in session_keys_to_clear:
        if key in request.session:
            del request.session[key]
    
    # Limpiar también cualquier otro código 2FA que pueda estar en sesión
    keys_to_remove = []
    for key in request.session.keys():
        if key.startswith('2fa_sent_'):
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del request.session[key]
    
    # Registrar logout
    try:
        SecureAccessLog.objects.create(
            user=request.user,
            access_code=access_code,
            success=True,
            action='logout',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    except Exception as e:
        logger.error(f"Error registrando logout: {e}")
    
    messages.info(request, "Sesión segura cerrada correctamente")
    return redirect('/')

@login_required
@csrf_exempt
def matrix_edit_view(request, access_code):
    """API para actualizar una celda de la matriz"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    # Verificar acceso autorizado
    if not validate_user_access(request.user):
        return JsonResponse({'success': False, 'error': 'Acceso no autorizado'})
    
    # Verificar que el usuario haya pasado por el proceso de autenticación
    if not request.session.get('secure_password_used'):
        return JsonResponse({'success': False, 'error': 'Debe autenticarse primero'})
    
    try:
        data = json.loads(request.body)
        
        # Verificar si es un guardado completo de matriz
        if 'matrix_data' in data:
            return save_complete_matrix(request, access_code, data['matrix_data'])
        
        # Si no, es actualización de celda individual
        row = int(data.get('row', 0))
        col = int(data.get('col', 0))
        value = str(data.get('value', ''))[:1000]  # Limitar longitud
        
        password_used = request.session.get('secure_password_used')
        password_hash = hashlib.sha256(password_used.encode()).hexdigest()
        is_decoy_mode = request.session.get('is_decoy_mode', False)
        
        # Actualizar o crear celda
        with transaction.atomic():
            cell, created = SecureDataMatrix.objects.get_or_create(
                password_hash=password_hash,
                row_index=row,
                col_index=col,
                defaults={
                    'data_type': 'decoy' if is_decoy_mode else 'real',
                    'encrypted_value': SecureDataMatrix.encrypt_data(value, password_hash)[0],
                    'encryption_salt': SecureDataMatrix.encrypt_data(value, password_hash)[1]
                }
            )
            
            if not created:
                encrypted_value, salt = SecureDataMatrix.encrypt_data(value, password_hash)
                cell.encrypted_value = encrypted_value
                cell.encryption_salt = salt
                cell.save()
        
        # Log de modificación
        SecureAccessLog.objects.create(
            user=request.user,
            access_code=access_code,
            success=True,
            action=f'cell_update_r{row}_c{col}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'row': row,
            'col': col,
            'value': value
        })
    
    except Exception as e:
        logger.error(f"Error updating cell: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Error interno del servidor'})

def save_complete_matrix(request, access_code, matrix_data):
    """Guardar matriz completa"""
    print(f"DEBUG: save_complete_matrix called with access_code: {access_code}")
    print(f"DEBUG: matrix_data type: {type(matrix_data)}, content: {matrix_data}")
    
    try:
        password_used = request.session.get('secure_password_used')
        print(f"DEBUG: password_used: {password_used}")
        
        if not password_used:
            print("ERROR: No password found in session")
            return JsonResponse({'success': False, 'error': 'Sesión inválida'})
            
        password_hash = hashlib.sha256(password_used.encode()).hexdigest()
        is_decoy_mode = request.session.get('is_decoy_mode', False)
        print(f"DEBUG: password_hash: {password_hash[:10]}..., is_decoy_mode: {is_decoy_mode}")
        
        cells_updated = 0
        
        with transaction.atomic():
            print(f"DEBUG: Starting transaction, processing {len(matrix_data)} rows")
            for row_index, row_data in matrix_data.items():
                print(f"DEBUG: Processing row {row_index} with {len(row_data)} cells")
                for col_index, value in row_data.items():
                    if value and str(value).strip():  # Solo guardar celdas con contenido
                        print(f"DEBUG: Saving cell ({row_index}, {col_index}) = '{value}'")
                        cell, created = SecureDataMatrix.objects.get_or_create(
                            password_hash=password_hash,
                            row_index=int(row_index),
                            col_index=int(col_index),
                            defaults={
                                'data_type': 'decoy' if is_decoy_mode else 'real',
                                'encrypted_value': SecureDataMatrix.encrypt_data(str(value), password_hash)[0],
                                'encryption_salt': SecureDataMatrix.encrypt_data(str(value), password_hash)[1]
                            }
                        )
                        
                        if not created:
                            encrypted_value, salt = SecureDataMatrix.encrypt_data(str(value), password_hash)
                            cell.encrypted_value = encrypted_value
                            cell.encryption_salt = salt
                            cell.save()
                        
                        cells_updated += 1
                        print(f"DEBUG: Cell saved successfully, total cells_updated: {cells_updated}")
        
        print(f"DEBUG: Transaction completed, creating access log")
        # Log de guardado completo
        SecureAccessLog.objects.create(
            user=request.user,
            access_code=access_code,
            success=True,
            action='matrix_save',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        print(f"DEBUG: Successfully saved {cells_updated} cells")
        return JsonResponse({
            'success': True,
            'cells_updated': cells_updated,
            'message': f'Matriz guardada exitosamente: {cells_updated} celdas actualizadas'
        })
        
    except Exception as e:
        print(f"ERROR: Exception in save_complete_matrix: {str(e)}")
        print(f"ERROR: Exception type: {type(e)}")
        import traceback
        print(f"ERROR: Traceback: {traceback.format_exc()}")
        logger.error(f"Error saving complete matrix: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Error interno del servidor'})

@login_required
@csrf_exempt
def load_cells(request, access_code):
    """API para cargar celdas dinámicamente (scroll infinito)"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    # Verificar acceso autorizado
    if not validate_user_access(request.user):
        return JsonResponse({'success': False, 'error': 'Acceso no autorizado'})
    
    # Verificar que el usuario haya pasado por el proceso de autenticación
    if not request.session.get('secure_password_used'):
        return JsonResponse({'success': False, 'error': 'Debe autenticarse primero'})
    
    try:
        data = json.loads(request.body)
        start_row = int(data.get('start_row', 0))
        end_row = int(data.get('end_row', 50))
        start_col = int(data.get('start_col', 0))
        end_col = int(data.get('end_col', 26))
        
        password_used = request.session.get('secure_password_used')
        password_hash = hashlib.sha256(password_used.encode()).hexdigest()
        
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
def matrix_download_view(request, access_code):
    return JsonResponse({'status': 'test', 'access_code': access_code})

@login_required
def matrix_upload_view(request, access_code):
    return JsonResponse({'status': 'test', 'access_code': access_code})
