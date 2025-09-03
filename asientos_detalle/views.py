from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import AsientoDetalle
from .forms import AsientoDetalleForm
import logging

logger = logging.getLogger(__name__)

@login_required
def detalle_list(request):
    """Lista todos los detalles de asientos"""
    try:
        # Obtener parámetros de filtrado
        search = request.GET.get('search', '')
        asiento = request.GET.get('asiento', '')
        
        # Query base
        detalles = AsientoDetalle.objects.select_related('asiento', 'cuenta', 'empresa_id').all()
        
        # Aplicar filtros
        if search:
            detalles = detalles.filter(
                Q(asiento__descripcion__icontains=search) |
                Q(cuenta__descripcion__icontains=search) |
                Q(empresa_id__nombre__icontains=search)
            )
        
        if asiento:
            detalles = detalles.filter(asiento_id=asiento)
        
        # Ordenar por fecha de asiento y empresa
        detalles = detalles.order_by('-asiento__fecha', 'empresa_id__nombre')
        
        # Estadísticas
        stats = {
            'total': detalles.count(),
            'total_debe': sum(detalle.valor for detalle in detalles if detalle.polaridad == '+'),
            'total_haber': sum(detalle.valor for detalle in detalles if detalle.polaridad == '-'),
            'empresas': detalles.values('empresa_id__nombre').distinct().count(),
        }
        
        # Paginación
        paginator = Paginator(detalles, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'detalles': page_obj,
            'stats': stats,
            'search': search,
            'asiento_filter': asiento,
        }
        
        return render(request, 'asientos_detalle/detalle_list.html', context)
        
    except Exception as e:
        logger.error(f"Error al cargar los detalles de asientos: {e}")
        messages.error(request, "Error al cargar los detalles de asientos")
        return render(request, 'asientos_detalle/detalle_list.html', {'detalles': []})

@login_required
def detalle_create(request):
    """Crear un nuevo detalle de asiento"""
    if request.method == 'POST':
        form = AsientoDetalleForm(request.POST)
        if form.is_valid():
            try:
                detalle = form.save()
                messages.success(
                    request, 
                    f'Detalle de asiento creado exitosamente'
                )
                return redirect('asientos_detalle:detalle_list')
                
            except Exception as e:
                logger.error(f"Error al crear detalle de asiento: {e}")
                messages.error(request, "Error interno al crear el detalle de asiento")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario")
    else:
        form = AsientoDetalleForm()
    
    context = {
        'form': form,
        'title': 'Crear Detalle de Asiento',
        'button_text': 'Crear Detalle'
    }
    
    return render(request, 'asientos_detalle/detalle_form.html', context)

@login_required
def detalle_edit(request, id):
    """Editar un detalle de asiento existente"""
    detalle = get_object_or_404(AsientoDetalle, id=id)
    
    if request.method == 'POST':
        form = AsientoDetalleForm(request.POST, instance=detalle)
        if form.is_valid():
            try:
                form.save()
                messages.success(
                    request, 
                    f'Detalle de asiento actualizado exitosamente'
                )
                return redirect('asientos_detalle:detalle_list')
                
            except Exception as e:
                logger.error(f"Error al actualizar detalle de asiento: {e}")
                messages.error(request, "Error interno al actualizar el detalle de asiento")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario")
    else:
        form = AsientoDetalleForm(instance=detalle)
    
    context = {
        'form': form,
        'detalle': detalle,
        'title': 'Editar Detalle de Asiento',
        'button_text': 'Actualizar Detalle'
    }
    
    return render(request, 'asientos_detalle/detalle_form.html', context)

@login_required
def detalle_delete(request, id):
    """Eliminar un detalle de asiento"""
    detalle = get_object_or_404(AsientoDetalle, id=id)
    
    if request.method == 'POST':
        try:
            detalle.delete()
            messages.success(request, "Detalle de asiento eliminado exitosamente")
            return redirect('asientos_detalle:detalle_list')
            
        except Exception as e:
            logger.error(f"Error al eliminar detalle de asiento: {e}")
            messages.error(request, "Error al eliminar el detalle de asiento")
            return redirect('asientos_detalle:detalle_list')
    
    context = {
        'detalle': detalle,
        'title': 'Eliminar Detalle de Asiento'
    }
    
    return render(request, 'asientos_detalle/detalle_confirm_delete.html', context)

@login_required
def detalle_detail(request, id):
    """Ver detalles de un detalle de asiento"""
    detalle = get_object_or_404(AsientoDetalle, id=id)
    
    context = {
        'detalle': detalle,
        'title': 'Detalle de Asiento'
    }
    
    return render(request, 'asientos_detalle/detalle_detail.html', context)
