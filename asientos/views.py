from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.db import transaction
from django.core.exceptions import ValidationError
import json
import logging
from .models import Asiento
from .forms import AsientoForm
from asientos_detalle.models import AsientoDetalle
from asientos_detalle.forms import AsientoDetalleForm
from plan_cuentas.models import PlanCuenta, Cuenta
from perfiles.models import Perfil, PerfilPlanCuenta

# Configurar logger para debugging
logger = logging.getLogger(__name__)

@login_required
def asiento_list(request):
    asientos = Asiento.objects.select_related('id_perfil').prefetch_related('detalles__cuenta').order_by('-fecha')
    return render(request, 'asientos/asiento_list.html', {'asientos': asientos})

@login_required
def asiento_detail(request, id):
    asiento = get_object_or_404(Asiento, pk=id)
    detalles = AsientoDetalle.objects.filter(asiento=asiento)
    
    monto_total = 0
    for detalle in detalles:
        if detalle.monto is not None:
            if detalle.polaridad == '+':
                monto_total += detalle.monto
            elif detalle.polaridad == '-':
                monto_total -= detalle.monto

    return render(request, 'asientos/asiento_detail.html', {
        'asiento': asiento,
        'detalles': detalles,
        'monto_total': monto_total
    })

@login_required
def asiento_create(request):
    if request.method == 'POST':
        form = AsientoForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    asiento_id_provisional = request.POST.get('asiento_id_provisional')
                    asiento = form.save(commit=False)
                    if asiento_id_provisional:
                        asiento.id = asiento_id_provisional
                    # id_perfil is now handled by the form, no need to set it manually
                    asiento.save()
                    return JsonResponse({
                        'success': True,
                        'asiento_id': asiento.id
                    })
            except ValidationError as e:
                return JsonResponse({
                    'success': False,
                    'error': "; ".join(e.messages) if hasattr(e, 'messages') else str(e)
                })
        else:
            errors = form.errors.as_json()
            parsed_errors = json.loads(errors)
            error_messages = []
            for field, field_errors in parsed_errors.items():
                for error_item in field_errors:
                    error_messages.append(f"{field if field != '__all__' else 'General'}: {error_item['message']}")
            return JsonResponse({
                'success': False,
                'error': "; ".join(error_messages)
            })
    else:
        form = AsientoForm(user=request.user)
    
    perfiles_list = Perfil.objects.all()
    plan_cuentas = PlanCuenta.objects.none()

    import datetime
    import hashlib
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    asiento_id_provisional = hashlib.sha256(f"TEMP-{timestamp}".encode()).hexdigest()
    
    context = {
        'form': form,
        'id': asiento_id_provisional,
        'asiento_id_provisional': asiento_id_provisional,
        'button_text': 'Crear Asiento',
        'perfiles_list': perfiles_list,
        'plan_cuentas': plan_cuentas
    }
    return render(request, 'asientos/form.html', context)

@login_required
def asiento_edit(request, id):
    asiento = get_object_or_404(Asiento, pk=id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Actualizar información básica del asiento
                asiento.fecha = request.POST.get('fecha')
                if request.POST.get('id_perfil'):
                    asiento.id_perfil_id = request.POST.get('id_perfil')
                asiento.descripcion = request.POST.get('descripcion', '')
                asiento.usuario_modificacion = request.user
                
                # Procesar los detalles
                total_detalles = int(request.POST.get('total_detalles', 0))
                total_debe = 0
                total_haber = 0
                
                # Eliminar detalles existentes
                AsientoDetalle.objects.filter(asiento=asiento).delete()
                
                # Crear nuevos detalles
                for i in range(total_detalles):
                    cuenta_id = request.POST.get(f'detalle_{i}_cuenta_id')
                    tipo = request.POST.get(f'detalle_{i}_tipo')
                    monto = float(request.POST.get(f'detalle_{i}_monto', 0))
                    
                    if cuenta_id and monto > 0:
                        # Obtener la cuenta
                        cuenta = Cuenta.objects.get(id=cuenta_id)
                        
                        # Determinar la polaridad basada en el tipo
                        if tipo == 'debe':
                            polaridad = '+'
                            total_debe += monto
                        else:
                            polaridad = '-'
                            total_haber += monto
                        
                        # Crear el detalle
                        # Obtener la empresa como objeto si existe
                        try:
                            from empresas.models import Empresa
                            empresa_obj = Empresa.objects.filter(nombre=asiento.empresa).first()
                        except:
                            empresa_obj = None
                        
                        AsientoDetalle.objects.create(
                            asiento=asiento,
                            cuenta=cuenta,
                            valor=monto,
                            polaridad=polaridad,
                            tipo_cuenta='DEBE' if tipo == 'debe' else 'HABER',
                            empresa_id=empresa_obj
                        )
                
                # Validar balance
                if abs(total_debe - total_haber) >= 0.01:
                    raise ValidationError('El asiento debe estar balanceado')
                
                # Guardar el asiento
                asiento.save()
                
                messages.success(request, 'Asiento contable actualizado exitosamente')
                return redirect('asientos:asiento_detail', id=asiento.id)
                
        except Exception as e:
            logger.error(f"Error actualizando asiento: {str(e)}")
            messages.error(request, f'Error al actualizar el asiento: {str(e)}')
    
    # GET request - mostrar formulario de edición
    form = AsientoForm(instance=asiento, user=request.user)
    perfiles = Perfil.objects.all()
    
    context = {
        'form': form,
        'id': id,
        'asiento_id_provisional': id,
        'button_text': 'Actualizar Asiento',
        'perfiles': perfiles,
        'is_edit_mode': True,
        'asiento': asiento
    }
    return render(request, 'asientos/asiento_create.html', context)

@login_required
def get_asiento_detalles(request, asiento_id):
    """
    Endpoint para obtener los detalles de un asiento existente en formato JSON
    """
    try:
        asiento = get_object_or_404(Asiento, pk=asiento_id)
        detalles = AsientoDetalle.objects.filter(asiento=asiento).select_related('cuenta')
        
        detalles_data = []
        for detalle in detalles:
            detalles_data.append({
                'id': detalle.id,
                'perfil_id': asiento.id_perfil.id if asiento.id_perfil else '',
                'cuenta_codigo': detalle.cuenta.cuenta if detalle.cuenta else '',
                'cuenta_descripcion': detalle.cuenta.descripcion if detalle.cuenta else '',
                'causa': detalle.DetalleDeCausa or '',
                'referencia': detalle.Referencia or '',
                'valor': float(detalle.valor) if detalle.valor else 0,
                'polaridad': detalle.polaridad,
                'tipo_cuenta': detalle.tipo_cuenta
            })
        
        return JsonResponse({
            'success': True,
            'detalles': detalles_data,
            'asiento': {
                'id': asiento.id,
                'numero': asiento.numero,
                'fecha': asiento.fecha.strftime('%Y-%m-%d'),
                'descripcion': asiento.descripcion,
                'perfil_id': asiento.id_perfil.id if asiento.id_perfil else ''
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def asiento_delete(request, id):
    asiento = get_object_or_404(Asiento, pk=id)
    if request.method == 'POST':
        asiento.delete()
        return redirect('asientos:asiento_list')
    return render(request, 'asientos/confirm_delete.html', {'asiento': asiento})

@login_required
def add_detalle(request, asiento_id):
    asiento = get_object_or_404(Asiento, pk=asiento_id)
    
    logger.debug(f"DEPURACIÓN ADD_DETALLE: Asiento ID: {asiento_id}, Método: {request.method}")
    
    if request.method == 'POST':
        logger.debug(f"DEPURACIÓN ADD_DETALLE: POST data: {request.POST}")
        
        form = AsientoDetalleForm(request.POST)
        logger.debug(f"DEPURACIÓN ADD_DETALLE: Form is_valid: {form.is_valid()}")
        
        if form.is_valid():
            logger.debug(f"DEPURACIÓN ADD_DETALLE: Form cleaned_data: {form.cleaned_data}")
            
            detalle = form.save(commit=False)
            detalle.asiento = asiento
            
            logger.debug(f"DEPURACIÓN ADD_DETALLE: Antes de guardar - Detalle: {detalle}")
            logger.debug(f"DEPURACIÓN ADD_DETALLE: Detalle.asiento: {detalle.asiento}")
            logger.debug(f"DEPURACIÓN ADD_DETALLE: Detalle.asiento: {detalle.ac_head_id}")
            logger.debug(f"DEPURACIÓN ADD_DETALLE: Detalle.tipo_cuenta: {detalle.tipo_cuenta}")
            logger.debug(f"DEPURACIÓN ADD_DETALLE: Detalle.cuenta: {detalle.cuenta}")
            logger.debug(f"DEPURACIÓN ADD_DETALLE: Detalle.monto: {detalle.monto}")
            logger.debug(f"DEPURACIÓN ADD_DETALLE: Detalle.polaridad: {detalle.polaridad}")
            
            try:
                detalle.save()
                logger.debug(f"DEPURACIÓN ADD_DETALLE: Detalle guardado exitosamente con ID: {detalle.id}")
                return redirect('asientos:asiento_detail', id=asiento_id)
            except Exception as e:
                logger.error(f"DEPURACIÓN ADD_DETALLE: Error al guardar detalle: {str(e)}")
                form.add_error(None, f"Error al guardar: {str(e)}")
        else:
            logger.debug(f"DEPURACIÓN ADD_DETALLE: Errores en formulario: {form.errors}")
    else:
        form = AsientoDetalleForm()
        logger.debug(f"DEPURACIÓN ADD_DETALLE: Formulario GET inicializado")
    
    context = {
        'form': form,
        'asiento': asiento,
        'button_text': 'Agregar Detalle'
    }
    return render(request, 'asientos/detalle_form.html', context)

@login_required
def edit_detalle(request, asiento_id, detalle_id):
    asiento = get_object_or_404(Asiento, pk=asiento_id)
    detalle = get_object_or_404(AsientoDetalle, pk=detalle_id, asiento=asiento)
    
    logger.debug(f"DEPURACIÓN: Editando detalle - ID: {detalle_id}, Tipo: {detalle.tipo_cuenta}")
    logger.debug(f"DEPURACIÓN: Valores iniciales - Monto: {detalle.monto}, Asiento: {detalle.ac_head_id}")
    
    if request.method == 'POST':
        form = AsientoDetalleForm(request.POST, instance=detalle)
        if form.is_valid():
            detalle_updated = form.save()
            logger.debug(f"DEPURACIÓN: Valores actualizados - Monto: {detalle_updated.monto}, Tipo: {detalle_updated.tipo_cuenta}, Perfil: {detalle_updated.perfil}")
            return redirect('asientos:asiento_detail', id=asiento_id)
        else:
            logger.debug(f"DEPURACIÓN: Errores en formulario: {form.errors}")
    else:
        form = AsientoDetalleForm(instance=detalle)
        logger.debug(f"DEPURACIÓN: Monto en formulario: {form['monto'].value()}")
        logger.debug(f"DEPURACIÓN: Asiento asociado: {detalle.ac_head_id}")
    
    context = {
        'form': form,
        'asiento': asiento,
        'detalle': detalle,
        'button_text': 'Actualizar Detalle'
    }
    return render(request, 'asientos/detalle_form.html', context)

@login_required
def delete_detalle(request, asiento_id, detalle_id):
    asiento = get_object_or_404(Asiento, pk=asiento_id)
    detalle = get_object_or_404(AsientoDetalle, pk=detalle_id, asiento=asiento)
    if request.method == 'POST':
        detalle.delete()
        return redirect('asientos:asiento_detail', id=asiento_id)
    return render(request, 'asientos/detalle_confirm_delete.html', {
        'asiento': asiento,
        'detalle': detalle
    })

@login_required
def add_detalles_bulk(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        asiento_id = request.POST.get('asiento_id')
        detalles_json = request.POST.get('detalles')
        
        if not asiento_id or not detalles_json:
            return JsonResponse({'success': False, 'error': 'Faltan datos requeridos'})
        
        asiento = get_object_or_404(Asiento, pk=asiento_id)
        detalles_nuevos_data = json.loads(detalles_json)
        
        with transaction.atomic():
            AsientoDetalle.objects.filter(asiento=asiento).delete()
            
            for detalle_data in detalles_nuevos_data:
                polaridad_configurada = detalle_data.get('polaridad')
                tipo_cuenta = ''
                if polaridad_configurada == '+':
                    tipo_cuenta = 'DEBE'
                elif polaridad_configurada == '-':
                    tipo_cuenta = 'HABER'
                else:
                    raise ValidationError(f"Polaridad inválida o no especificada: {polaridad_configurada} para cuenta {detalle_data.get('cuenta')}")

                perfil_id = detalle_data.get('perfil_id')
                if not perfil_id:
                    raise ValidationError("Falta el ID del perfil para el detalle.")
                
                try:
                    perfil_obj = Perfil.objects.get(id=perfil_id)
                except Perfil.DoesNotExist:
                    raise ValidationError(f"El perfil con ID {perfil_id} no existe.")

                cuenta_codigo = detalle_data.get('cuenta', '')
                try:
                    # Buscar la cuenta por código usando el campo 'cuenta'
                    cuenta_obj = Cuenta.objects.get(cuenta=cuenta_codigo)
                except Cuenta.DoesNotExist:
                    raise ValidationError(f"La cuenta {cuenta_codigo} no existe en el plan de cuentas (Perfil: {perfil_obj.nombre}).")

                # Obtener la empresa como objeto si existe
                try:
                    from empresas.models import Empresa
                    empresa_obj = Empresa.objects.filter(nombre=asiento.empresa).first()
                except:
                    empresa_obj = None

                AsientoDetalle.objects.create(
                    asiento=asiento,
                    tipo_cuenta=tipo_cuenta, 
                    cuenta=cuenta_obj,
                    DetalleDeCausa=detalle_data.get('causa', ''),
                    Referencia=detalle_data.get('Referencia', ''),
                    valor=float(detalle_data.get('monto', 0)),
                    polaridad=polaridad_configurada,
                    empresa_id=empresa_obj
                )

            # Calcular el total después de crear todos los detalles
            total_movimientos = 0
            detalles_guardados = AsientoDetalle.objects.filter(asiento=asiento)
            
            # Logging detallado para cada detalle
            logger.info(f"=== DEPURACIÓN BALANCE ASIENTO {asiento.id} ===")
            logger.info(f"Número de detalles encontrados: {detalles_guardados.count()}")
            
            for i, detalle_obj in enumerate(detalles_guardados, 1):
                if detalle_obj.monto is not None:
                    monto_actual = float(detalle_obj.monto)
                    polaridad_actual = detalle_obj.polaridad
                    
                    logger.info(f"Detalle {i}: Monto={monto_actual}, Polaridad='{polaridad_actual}', Tipo={detalle_obj.tipo_cuenta}")
                    
                    if polaridad_actual == '+':
                        total_movimientos += monto_actual
                        logger.info(f"  Sumando {monto_actual} (total parcial: {total_movimientos})")
                    elif polaridad_actual == '-':
                        total_movimientos -= monto_actual
                        logger.info(f"  Restando {monto_actual} (total parcial: {total_movimientos})")
                    else:
                        logger.warning(f"  Polaridad desconocida: '{polaridad_actual}'")
                else:
                    logger.warning(f"Detalle {i}: Monto es None")
            
            logger.info(f"TOTAL FINAL CALCULADO: {total_movimientos}")
            logger.info(f"TOTAL REDONDEADO: {round(total_movimientos, 2)}")
            logger.info(f"¿ES IGUAL A CERO?: {round(total_movimientos, 2) == 0}")
            logger.info("=== FIN DEPURACIÓN BALANCE ===")
            
            if round(total_movimientos, 2) != 0:
                error_msg = f"La suma de los movimientos (debe y haber) debe ser igual a cero. Total: {total_movimientos:.2f}"
                logger.error(f"BALANCE NO EQUILIBRADO: {error_msg}")
                raise ValidationError(error_msg)
            else:
                logger.info("BALANCE EQUILIBRADO: El asiento está balanceado correctamente")
        
        return JsonResponse({'success': True, 'asiento_id': asiento.id})
    
    except ValidationError as e:
        logger.error(f"ValidationError in add_detalles_bulk: {e.message_dict if hasattr(e, 'message_dict') else e.messages}")
        error_msg = "; ".join(e.messages) if hasattr(e, 'messages') else str(e)
        return JsonResponse({'success': False, 'error': error_msg})
    except json.JSONDecodeError:
        logger.error("Error decoding JSON in add_detalles_bulk", exc_info=True)
        return JsonResponse({'success': False, 'error': 'Formato JSON inválido en los detalles.'})
    except Exception as e:
        logger.error(f"Error in add_detalles_bulk: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': f'Ocurrió un error procesando los detalles: {str(e)}'})

@login_required
def get_cuentas_for_perfil(request, perfil_id):
    try:
        perfil = Perfil.objects.get(id=perfil_id)
        configuraciones = PerfilPlanCuenta.objects.filter(perfil_id=perfil_id).select_related('cuentas_id')
        
        cuentas_data = []
        for config in configuraciones:
            cuentas_data.append({
                'id': config.cuentas_id.pk,
                'cuenta': config.cuentas_id.cuenta,
                'descripcion': config.cuentas_id.descripcion,
                'polaridad': config.polaridad
            })
        
        return JsonResponse({'success': True, 'cuentas': cuentas_data})
    except Perfil.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Perfil no encontrado'}, status=404)
    except Exception as e:
        logger.error(f"Error in get_cuentas_for_perfil: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': f'Error interno del servidor: {str(e)}'}, status=500)

def secure_login_view(request):
    """Vista de login para el modo seguro"""
    context = {
        'is_secure_login_page': True,
        'is_auth_page': True,  # Identificador adicional
    }
    
    if request.method == 'POST':
        # Lógica de login aquí
        pass
    
    return render(request, 'secure/login.html', context)

def secure_auth_view(request):
    """Vista de autenticación 2FA para modo seguro"""
    context = {
        'is_secure_login_page': False,
        'is_auth_page': True,  # Es página de autenticación
    }
    
    if request.method == 'POST':
        # Lógica de autenticación aquí
        pass
    
    return render(request, 'secure/auth.html', context)

@login_required
def secure_data_view(request):
    """Vista principal del modo seguro con autenticación por contraseña"""
    
    # Lista de contraseñas válidas para desarrollo
    valid_passwords = [
        'DataView2024!',
        'SecureInfo#99', 
        'AccessMatrix@1',
        'Qwerty01*+',
        'TrueInfo#Secret99',
        'AuthMatrix@Real1'
    ]
    
    if request.method == 'POST':
        password = request.POST.get('secure_password', '').strip()
        
        if password in valid_passwords:
            # Contraseña válida, establecer sesión
            request.session['secure_authenticated'] = True
            request.session['secure_password_used'] = password
            
            # Determinar tipo de datos según contraseña
            is_real_data = password in ['Qwerty01*+', 'TrueInfo#Secret99', 'AuthMatrix@Real1']
            request.session['show_real_data'] = is_real_data
            
            logger.info(f"Acceso seguro exitoso para usuario {request.user.email} con contraseña: {password}")
            messages.success(request, 'Acceso autorizado al modo seguro')
            
            return redirect('secure_dashboard')
        else:
            messages.error(request, 'Contraseña incorrecta. Acceso denegado.')
            logger.warning(f"Intento de acceso fallido para usuario {request.user.email}")
    
    return render(request, 'secure/login.html', {
        'user': request.user,
        'dev_mode': True  # Flag para mostrar ayudas en desarrollo
    })

@login_required
def secure_dashboard_view(request):
    """Dashboard del modo seguro"""
    
    # Verificar autenticación del modo seguro
    if not request.session.get('secure_authenticated', False):
        messages.warning(request, 'Debe autenticarse en el modo seguro primero')
        return redirect('secure_data')
    
    show_real_data = request.session.get('show_real_data', False)
    password_used = request.session.get('secure_password_used', '')
    
    # Datos simulados según el tipo de contraseña
    if show_real_data:
        data_matrix = [
            ['OPERACIÓN ALPHA', '$2,500,000', 'CONFIDENCIAL', 'En proceso'],
            ['CONTACTO BETA', '$5,800,000', 'ULTRA-SECRETO', 'Aprobado'],
            ['PROYECTO GAMMA', '$12,000,000', 'ALTO RIESGO', 'Pendiente']
        ]
    else:
        data_matrix = [
            ['Proyecto Demo', '$50,000', 'Público', 'Completado'],
            ['Cliente Test', '$25,000', 'Normal', 'Pendiente'],
            ['Operación Prueba', '$15,000', 'Estándar', 'En revisión']
        ]
    
    context = {
        'data_matrix': data_matrix,
        'show_real_data': show_real_data,
        'password_used': password_used,
        'user': request.user
    }
    
    return render(request, 'secure/dashboard.html', context)

@login_required
def asiento_create_new(request):
    """
    Nueva vista para crear asientos contables con interfaz mejorada
    """
    if request.method == 'POST':
        try:
            with transaction.atomic():
                logger.debug(f"=== DEPURACIÓN ASIENTO_CREATE_NEW ===")
                logger.debug(f"POST data: {dict(request.POST)}")
                logger.debug(f"POST keys: {list(request.POST.keys())}")
                
                # Validar que hay detalles
                total_detalles_str = request.POST.get('total_detalles', '0')
                logger.debug(f"Total detalles string: '{total_detalles_str}'")
                
                try:
                    total_detalles = int(total_detalles_str)
                except (ValueError, TypeError):
                    logger.error(f"Error convirtiendo total_detalles a int: '{total_detalles_str}'")
                    total_detalles = 0
                    
                logger.debug(f"Total detalles recibidos: {total_detalles}")
                
                # Contar detalles manualmente para verificar
                detalle_count = 0
                for key in request.POST.keys():
                    if key.startswith('detalle_') and key.endswith('_cuenta_id'):
                        if request.POST.get(key):  # Solo contar si tiene valor
                            detalle_count += 1
                logger.debug(f"Detalles contados manualmente: {detalle_count}")
                
                if total_detalles == 0:
                    logger.error(f"VALIDACIÓN FALLIDA: total_detalles=0, pero conteo manual={detalle_count}")
                    messages.error(request, f'Debe agregar al menos un detalle al asiento (recibido: {total_detalles}, contado: {detalle_count})')
                    perfiles = Perfil.objects.all()
                    return render(request, 'asientos/asiento_create.html', {
                        'perfiles': perfiles,
                        'is_edit_mode': False
                    })
                
                # Crear el asiento principal
                asiento = Asiento.objects.create(
                    fecha=request.POST.get('fecha'),
                    id_perfil_id=request.POST.get('id_perfil'),
                    descripcion=request.POST.get('descripcion', ''),
                    empresa='DEFAULT',
                    usuario_creacion=request.user
                )
                
                # Procesar los detalles
                total_debe = 0
                total_haber = 0
                
                for i in range(total_detalles):
                    cuenta_id = request.POST.get(f'detalle_{i}_cuenta_id')
                    tipo = request.POST.get(f'detalle_{i}_tipo')
                    monto_str = request.POST.get(f'detalle_{i}_monto', '0')
                    
                    logger.debug(f"Procesando detalle {i}: cuenta_id={cuenta_id}, tipo={tipo}, monto_str={monto_str}")
                    
                    try:
                        monto = float(monto_str)
                    except (ValueError, TypeError):
                        logger.error(f"Error convirtiendo monto a float: {monto_str}")
                        monto = 0
                    
                    if cuenta_id and monto > 0:
                        # Obtener la cuenta
                        try:
                            cuenta = Cuenta.objects.get(id=cuenta_id)
                        except Cuenta.DoesNotExist:
                            logger.error(f"Cuenta con ID {cuenta_id} no existe")
                            continue
                        
                        # Determinar la polaridad basada en el tipo
                        if tipo == 'debe':
                            polaridad = '+'
                            total_debe += monto
                        else:
                            polaridad = '-'
                            total_haber += monto
                        
                        # Obtener la empresa como objeto si existe
                        try:
                            from empresas.models import Empresa
                            empresa_obj = Empresa.objects.filter(nombre='DEFAULT').first()
                        except Exception:
                            empresa_obj = None
                        
                        # Crear el detalle
                        AsientoDetalle.objects.create(
                            asiento=asiento,
                            cuenta=cuenta,
                            valor=monto,
                            polaridad=polaridad,
                            tipo_cuenta='DEBE' if tipo == 'debe' else 'HABER',
                            empresa_id=empresa_obj
                        )
                        
                        logger.debug(f"Detalle creado: Cuenta={cuenta.cuenta}, Monto={monto}, Polaridad={polaridad}")
                
                # Validar balance
                if abs(total_debe - total_haber) >= 0.01:
                    raise ValidationError(f'El asiento debe estar balanceado. Total Debe: ${total_debe:.2f}, Total Haber: ${total_haber:.2f}')
                
                logger.info(f"Asiento creado exitosamente: {asiento.id} con {total_detalles} detalles")
                messages.success(request, 'Asiento contable creado exitosamente')
                return redirect('asientos:asiento_detail', id=asiento.id)
                
        except ValidationError as e:
            logger.error(f"Error de validación creando asiento: {str(e)}")
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"Error inesperado creando asiento: {str(e)}", exc_info=True)
            messages.error(request, f'Error inesperado al crear el asiento: {str(e)}')
    
    # GET request - mostrar formulario
    perfiles = Perfil.objects.all()
    return render(request, 'asientos/asiento_create.html', {
        'perfiles': perfiles,
        'is_edit_mode': False
    })

@login_required
def api_perfil_cuentas(request, perfil_id):
    """
    API endpoint para obtener las cuentas asociadas a un perfil
    """
    try:
        perfil = get_object_or_404(Perfil, id=perfil_id)
        perfil_cuentas = PerfilPlanCuenta.objects.filter(perfil_id=perfil).select_related('cuentas_id')
        
        cuentas = []
        for pc in perfil_cuentas:
            cuentas.append({
                'id': pc.cuentas_id.id,
                'codigo': pc.cuentas_id.cuenta,
                'descripcion': pc.cuentas_id.descripcion,
                'polaridad': pc.polaridad
            })
        
        return JsonResponse({
            'success': True,
            'cuentas': cuentas
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo cuentas del perfil {perfil_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
