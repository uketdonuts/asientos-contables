from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db import transaction, IntegrityError
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from .models import Empresa
from .forms import EmpresaForm, EmpresaFilterForm
import logging

logger = logging.getLogger(__name__)


@login_required
def empresa_list(request):
    """Lista todas las empresas del sistema"""
    try:
        # Obtener parámetros de filtrado
        search = request.GET.get('search', '')
        activa = request.GET.get('activa', '')
        tipo = request.GET.get('tipo', '')
        
        # Query base
        empresas = Empresa.objects.all()
        
        # Aplicar filtros
        if search:
            # Intentar búsqueda por ID si es un número
            search_filters = Q(nombre__icontains=search) | Q(descripcion__icontains=search)
            
            # Si el término de búsqueda es un número, buscar también por ID exacto
            if search.isdigit():
                search_filters = search_filters | Q(id=int(search))
            
            empresas = empresas.filter(search_filters)
        
        if activa:
            empresas = empresas.filter(activa=activa == 'true')
            
        if tipo:
            empresas = empresas.filter(type=tipo)
        
        # Ordenar por nombre
        empresas = empresas.order_by('nombre')
        
        # Estadísticas
        stats = {
            'total': empresas.count(),
            'activas': empresas.filter(activa=True).count(),
            'inactivas': empresas.filter(activa=False).count(),
            'tipos': empresas.values('type').annotate(count=Count('id')).order_by('type')
        }
        
        # Paginación
        paginator = Paginator(empresas, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'empresas': page_obj,
            'stats': stats,
            'search': search,
            'activa_filter': activa,
            'tipo_filter': tipo,
            'form_filter': EmpresaFilterForm(request.GET or None),
        }
        
        return render(request, 'empresas/list.html', context)
        
    except Exception as e:
        logger.error(f"Error al cargar las empresas: {e}")
        messages.error(request, "Error al cargar las empresas")
        return render(request, 'empresas/list.html', {'empresas': []})


@login_required
def empresa_create(request):
    """Crear una nueva empresa"""
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    empresa = form.save()
                    
                messages.success(
                    request, 
                    f'Empresa "{empresa.nombre}" creada exitosamente'
                )
                return redirect('empresas:empresa_list')
                
            except IntegrityError as e:
                logger.error(f"Error de integridad al crear empresa: {e}")
                messages.error(request, "Ya existe una empresa con ese ID")
            except Exception as e:
                logger.error(f"Error al crear empresa: {e}")
                messages.error(request, "Error interno al crear la empresa")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario")
    else:
        form = EmpresaForm()
    
    context = {
        'form': form,
        'title': 'Crear Empresa',
        'button_text': 'Crear Empresa'
    }
    
    return render(request, 'empresas/form.html', context)


@login_required
def empresa_edit(request, empresa_id):
    """Editar una empresa existente"""
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            try:
                with transaction.atomic():
                    empresa = form.save()
                    
                messages.success(
                    request, 
                    f'Empresa "{empresa.nombre}" actualizada exitosamente'
                )
                return redirect('empresas:empresa_list')
                
            except Exception as e:
                logger.error(f"Error al actualizar empresa: {e}")
                messages.error(request, "Error interno al actualizar la empresa")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario")
    else:
        form = EmpresaForm(instance=empresa)
    
    context = {
        'form': form,
        'title': f'Editar Empresa: {empresa.nombre}',
        'button_text': 'Actualizar Empresa',
        'empresa': empresa
    }
    
    return render(request, 'empresas/form.html', context)


@login_required
def empresa_detail(request, empresa_id):
    """Ver detalles de una empresa"""
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    # Obtener estadísticas relacionadas
    from plan_cuentas.models import PlanCuenta, Cuenta
    from asientos.models import Asiento
    
    stats = {
        'planes_cuentas': PlanCuenta.objects.filter(empresa=empresa.id).count(),
        'cuentas': Cuenta.objects.filter(empresa=empresa.id).count(),
        'asientos': Asiento.objects.filter(empresa=empresa.id).count(),
    }
    
    context = {
        'empresa': empresa,
        'stats': stats,
    }
    
    return render(request, 'empresas/detail.html', context)


@login_required
def empresa_delete(request, empresa_id):
    """Eliminar una empresa"""
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    if request.method == 'POST':
        try:
            # Verificar si la empresa tiene datos relacionados
            from plan_cuentas.models import PlanCuenta, Cuenta
            from asientos.models import Asiento
            
            if PlanCuenta.objects.filter(empresa=empresa.id).exists():
                messages.error(
                    request, 
                    f'No se puede eliminar la empresa "{empresa.nombre}" porque tiene planes de cuentas asociados'
                )
                return redirect('empresas:empresa_list')
            
            if Cuenta.objects.filter(empresa=empresa.id).exists():
                messages.error(
                    request, 
                    f'No se puede eliminar la empresa "{empresa.nombre}" porque tiene cuentas asociadas'
                )
                return redirect('empresas:empresa_list')
            
            if Asiento.objects.filter(empresa=empresa.id).exists():
                messages.error(
                    request, 
                    f'No se puede eliminar la empresa "{empresa.nombre}" porque tiene asientos contables asociados'
                )
                return redirect('empresas:empresa_list')
            
            with transaction.atomic():
                empresa_nombre = empresa.nombre
                empresa.delete()
                
            messages.success(
                request, 
                f'Empresa "{empresa_nombre}" eliminada exitosamente'
            )
            
        except Exception as e:
            logger.error(f"Error al eliminar empresa: {e}")
            messages.error(request, "Error interno al eliminar la empresa")
    
    return redirect('empresas:empresa_list')


@login_required
def empresa_toggle_active(request, empresa_id):
    """Activar/desactivar una empresa"""
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    if request.method == 'POST':
        try:
            empresa.activa = not empresa.activa
            empresa.save()
            
            estado = "activada" if empresa.activa else "desactivada"
            messages.success(
                request, 
                f'Empresa "{empresa.nombre}" {estado} exitosamente'
            )
            
        except Exception as e:
            logger.error(f"Error al cambiar estado de empresa: {e}")
            messages.error(request, "Error interno al cambiar el estado de la empresa")
    
    return redirect('empresas:empresa_list')


@login_required
def empresa_ajax_list(request):
    """Lista de empresas para uso en AJAX"""
    try:
        empresas = Empresa.objects.filter(activa=True).values('id', 'nombre').order_by('nombre')
        return JsonResponse(list(empresas), safe=False)
    except Exception as e:
        logger.error(f"Error en AJAX empresas: {e}")
        return JsonResponse({'error': 'Error al cargar empresas'}, status=500)
