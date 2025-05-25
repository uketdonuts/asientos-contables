from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
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
from plan_cuentas.models import PlanCuenta
from perfiles.models import Perfil, PerfilPlanCuenta

# Configurar logger para debugging
logger = logging.getLogger(__name__)

@login_required
def asiento_list(request):
    asientos = Asiento.objects.all().order_by('-fecha')
    return render(request, 'asientos/list.html', {'asientos': asientos})

@login_required
def asiento_detail(request, id):
    asiento = get_object_or_404(Asiento, pk=id)
    detalles = AsientoDetalle.objects.filter(asiento=asiento)
    
    # Calcular el monto total
    monto_total = sum(detalle.valor for detalle in detalles)
    
    return render(request, 'asientos/detail.html', {
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
                    # Si se envió un ID provisional, usarlo
                    asiento_id_provisional = request.POST.get('asiento_id_provisional')
                    asiento = form.save(commit=False)
                    if asiento_id_provisional:
                        asiento.id = asiento_id_provisional
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
                for error in field_errors:
                    error_messages.append(f"{field if field != '__all__' else 'General'}: {error['message']}")
            return JsonResponse({
                'success': False,
                'error': "; ".join(error_messages)
            })
    else:
        form = AsientoForm(user=request.user)
    
    # Generate a provisional ID based on timestamp
    import datetime
    import hashlib
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    asiento_id_provisional = hashlib.sha256(f"TEMP-{timestamp}".encode()).hexdigest()
    
    context = {
        'form': form,
        'id': asiento_id_provisional,
        'asiento_id_provisional': asiento_id_provisional,
        'button_text': 'Crear Asiento',
    }
    return render(request, 'asientos/form.html', context)

@login_required
def asiento_edit(request, id):
    asiento = get_object_or_404(Asiento, pk=id)
    if request.method == 'POST':
        form = AsientoForm(request.POST, instance=asiento, user=request.user)
        if form.is_valid():
            try:
                form.save()
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
                for error in field_errors:
                    error_messages.append(f"{field if field != '__all__' else 'General'}: {error['message']}")
            return JsonResponse({
                'success': False,
                'error': "; ".join(error_messages)
            })
    else:
        form = AsientoForm(instance=asiento, user=request.user)
    
    detalles = AsientoDetalle.objects.filter(asiento=asiento)
    
    # Log detalles values for debugging
    for detalle in detalles:
        logger.debug(f"Detalle ID: {detalle.id}, Tipo: {detalle.tipo_cuenta}, Valor: {detalle.valor}, Polaridad: {detalle.polaridad}")
    
    context = {
        'form': form,
        'id': id,
        'button_text': 'Actualizar Asiento',
        'detalles': detalles
    }
    return render(request, 'asientos/form.html', context)

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
    
    if request.method == 'POST':
        form = AsientoDetalleForm(request.POST)
        if form.is_valid():
            detalle = form.save(commit=False)
            detalle.asiento = asiento
            detalle.save()
            return redirect('asientos:asiento_detail', id=asiento_id)
    else:
        form = AsientoDetalleForm()
    
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
    
    # Añadir logs de depuración
    logger.debug(f"DEPURACIÓN: Editando detalle - ID: {detalle_id}, Tipo: {detalle.tipo_cuenta}")
    logger.debug(f"DEPURACIÓN: Valores iniciales - Valor: {detalle.valor}, Perfil: {asiento.perfil}")
    
    if request.method == 'POST':
        form = AsientoDetalleForm(request.POST, instance=detalle)
        if form.is_valid():
            detalle_updated = form.save(commit=False)
            
            # Añadir más logs de depuración
            logger.debug(f"DEPURACIÓN: Valores actualizados - Valor: {detalle_updated.valor}, Tipo: {detalle_updated.tipo_cuenta}")
            
            # Guardar el detalle actualizado
            detalle_updated.save()
            
            return redirect('asientos:asiento_detail', id=asiento_id)
        else:
            # Si hay errores, log para debugging
            logger.debug(f"DEPURACIÓN: Errores en formulario: {form.errors}")
    else:
        form = AsientoDetalleForm(instance=detalle)
        # Depuración del formulario
        logger.debug(f"DEPURACIÓN: Valor en formulario: {form['valor'].value()}")
        logger.debug(f"DEPURACIÓN: Valor del perfil asociado: {asiento.perfil}")
    
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
    """Add multiple asiento details in a single request."""
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
            # Clear existing details if any
            AsientoDetalle.objects.filter(asiento=asiento).delete()
            
            # Create new details
            for detalle_data in detalles_nuevos_data:
                # Corrected tipo_cuenta derivation based on new polaridad convention (DEBE '+', HABER '-')
                polaridad_configurada = detalle_data.get('polaridad')
                if polaridad_configurada == '+':
                    tipo_cuenta = 'DEBE'
                elif polaridad_configurada == '-':
                    tipo_cuenta = 'HABER'
                else:
                    # Handle cases where polaridad might be missing or invalid, though frontend should ensure it.
                    raise ValidationError(f"Polaridad inválida o no especificada: {polaridad_configurada}")

                try:
                    cuenta_codigo = detalle_data.get('cuenta', '')
                    cuenta_obj = PlanCuenta.objects.get(codigocuenta=cuenta_codigo, empresa=asiento.empresa)
                except PlanCuenta.DoesNotExist:
                    raise ValidationError(f"La cuenta {cuenta_codigo} no existe en el plan de cuentas para la empresa {asiento.empresa}.")

                if not polaridad_configurada: # Should be caught by earlier check, but as a safeguard.
                    raise ValidationError(f"No se especificó la polaridad para la cuenta {cuenta_codigo}.")

                detalle = AsientoDetalle(
                    asiento=asiento,
                    tipo_cuenta=tipo_cuenta, 
                    cuenta=cuenta_obj,
                    DetalleDeCausa=detalle_data.get('DetalleDeCausa', ''),
                    Referencia=detalle_data.get('Referencia', ''),
                    valor=float(detalle_data.get('valor', 0)), # Ensure value is float
                    polaridad=polaridad_configurada 
                )
                detalle.save()

            # After all details are created/updated, check the sum for the asiento
            total_movimientos = 0
            for detalle_obj in asiento.detalles.all(): # Re-fetch to ensure we have fresh data
                if detalle_obj.valor is not None:
                    if detalle_obj.polaridad == '+':
                        total_movimientos += detalle_obj.valor
                    elif detalle_obj.polaridad == '-':
                        total_movimientos -= detalle_obj.valor
            
            if total_movimientos != 0:
                # This will rollback the transaction
                raise ValidationError(f"La suma de los movimientos (debe y haber) debe ser igual a cero. Total: {total_movimientos}")
        
        return JsonResponse({'success': True, 'asiento_id': asiento.id})
    
    except ValidationError as e:
        # Log the validation error for debugging
        logger.error(f"ValidationError in add_detalles_bulk: {e.message_dict if hasattr(e, 'message_dict') else e.messages}")
        return JsonResponse({
            'success': False, 
            'error': e.message_dict if hasattr(e, 'message_dict') else "; ".join(e.messages)
        })
    except Exception as e:
        logger.error(f"Error in add_detalles_bulk: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'Ocurrió un error procesando los detalles.'})

@login_required
def get_cuentas_for_perfil(request, perfil_id):
    try:
        perfil = Perfil.objects.get(id=perfil_id)
        # Fetching PerfilPlanCuenta entries for the given perfil
        configuraciones = PerfilPlanCuenta.objects.filter(perfil=perfil).select_related('cuenta')
        
        cuentas_data = []
        for config in configuraciones:
            cuentas_data.append({
                'id': config.cuenta.pk,  # Using PlanCuenta's actual primary key if it's not codigocuenta
                'codigocuenta': config.cuenta.codigocuenta,
                'descripcion': config.cuenta.descripcion,
                'polaridad': config.polaridad  # This is the crucial part
            })
        
        return JsonResponse({'success': True, 'cuentas': cuentas_data})
    except Perfil.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Perfil no encontrado'}, status=404)
    except Exception as e:
        logger.error(f"Error in get_cuentas_for_perfil: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
