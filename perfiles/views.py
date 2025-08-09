from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db import transaction, IntegrityError
from .models import Perfil
from .forms import PerfilForm
import logging

logger = logging.getLogger(__name__)

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
    if request.method == 'POST':
        form = PerfilForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    perfil = form.save(commit=False)
                    # El usuario_creacion puede ser agregado si existe el campo
                    if hasattr(perfil, 'usuario_creacion'):
                        perfil.usuario_creacion = request.user
                    perfil.save()
                    
                messages.success(
                    request, 
                    f'Perfil "{perfil.nombre}" creado exitosamente'
                )
                return redirect('perfiles:perfil_list')
            
            except IntegrityError as e:
                logger.error(f"Error de integridad al crear perfil: {e}")
                messages.error(request, "Ya existe un perfil con ese nombre")
            except Exception as e:
                logger.error(f"Error al crear perfil: {e}")
                messages.error(request, "Error interno al crear el perfil contable")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario")
    else:
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
