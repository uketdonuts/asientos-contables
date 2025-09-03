from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db import transaction, IntegrityError
from django.http import JsonResponse
from .models import Perfil
from .forms import PerfilForm
import logging

logger = logging.getLogger('perfiles')

@login_required
def perfil_list(request):
    """Lista todos los perfiles contables"""
    try:
        perfiles = Perfil.objects.all().order_by('id')
        return render(request, 'perfiles/list.html', {'perfiles': perfiles})
    except Exception as e:
        logger.error(f"Error al cargar la lista de perfiles: {e}")
        messages.error(request, "Error al cargar los perfiles contables")
        return render(request, 'perfiles/list.html', {'perfiles': []})

@login_required
def perfil_create(request):
    """Crear un nuevo perfil contable"""
    logger.debug(f"Usuario {request.user} accediendo a perfil_create con método {request.method}")
    
    if request.method == 'POST':
        logger.debug(f"POST request recibido para crear perfil")
        logger.debug(f"POST data: {dict(request.POST)}")
        
        # Validar CSRF token manualmente
        from django.middleware.csrf import get_token
        csrf_token = get_token(request)
        logger.debug(f"CSRF token válido: {csrf_token}")
        
        form = PerfilForm(request.POST)
        
        logger.debug(f"Form is_valid: {form.is_valid()}")
        if not form.is_valid():
            logger.error(f"Form errors: {form.errors}")
            for field, errors in form.errors.items():
                logger.error(f"Field {field}: {errors}")
            
        if form.is_valid():
            logger.debug("Formulario válido, intentando guardar")
            try:
                # Crear el perfil manualmente para debug
                nombre = form.cleaned_data['nombre']
                descripcion = form.cleaned_data.get('descripcion', '')
                
                logger.debug(f"Creando perfil: nombre={nombre}, descripcion={descripcion}")
                
                perfil = Perfil(nombre=nombre, descripcion=descripcion)
                logger.debug(f"Perfil creado en memoria: {perfil}")
                
                perfil.save()
                logger.debug(f"Perfil guardado exitosamente con ID: {perfil.id}")
                    
                messages.success(
                    request, 
                    f'Perfil "{perfil.nombre}" creado exitosamente'
                )
                logger.info(f"Perfil '{perfil.nombre}' creado exitosamente")
                return redirect('perfiles:perfil_list')
            
            except IntegrityError as e:
                logger.error(f"Error de integridad al crear perfil: {e}")
                messages.error(request, "Ya existe un perfil con ese nombre")
            except Exception as e:
                logger.error(f"Error inesperado al crear perfil: {e}", exc_info=True)
                messages.error(request, f"Error interno al crear el perfil contable: {str(e)}")
        else:
            # Log de errores detallados de formulario
            logger.warning(f"Errores de formulario al crear perfil: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        logger.debug("GET request para crear perfil")
        form = PerfilForm()
    
    context = {
        'form': form,
        'id': None,
        'button_text': 'Crear'
    }
    return render(request, 'perfiles/form.html', context)

@login_required
def perfil_edit(request, id):
    """Editar un perfil contable existente"""
    perfil = get_object_or_404(Perfil, pk=id)
    
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            try:
                with transaction.atomic():
                    perfil_actualizado = form.save()
                    
                messages.success(
                    request, 
                    f'Perfil "{perfil_actualizado.nombre}" actualizado exitosamente'
                )
                return redirect('perfiles:perfil_list')
            
            except IntegrityError as e:
                logger.error(f"Error de integridad al actualizar perfil: {e}")
                messages.error(request, "Ya existe un perfil con ese nombre")
            except Exception as e:
                logger.error(f"Error al actualizar perfil: {e}")
                messages.error(request, "Error interno al actualizar el perfil contable")
        else:
            # Log de errores detallados de formulario
            try:
                logger.warning(f"Errores de formulario al actualizar perfil {perfil.pk}: {form.errors.as_json()}")
            except Exception:
                logger.warning(f"Errores de formulario al actualizar perfil {perfil.pk}: {form.errors}")
            messages.error(request, "Por favor corrija los errores en el formulario")
    else:
        form = PerfilForm(instance=perfil)
    
    context = {
        'form': form,
        'id': id,
        'perfil': perfil,
        'button_text': 'Actualizar'
    }
    return render(request, 'perfiles/form.html', context)

@login_required
def perfil_delete(request, id):
    """Eliminar un perfil contable"""
    perfil = get_object_or_404(Perfil, pk=id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                nombre = perfil.nombre
                perfil.delete()
                
            messages.success(
                request, 
                f'Perfil "{nombre}" eliminado exitosamente'
            )
            return redirect('perfiles:perfil_list')
            
        except Exception as e:
            logger.error(f"Error al eliminar perfil: {e}")
            messages.error(
                request, 
                "No se puede eliminar el perfil. Puede tener configuraciones o asientos asociados."
            )
            return redirect('perfiles:perfil_list')
    
    return render(request, 'perfiles/confirm_delete.html', {'perfil': perfil})
