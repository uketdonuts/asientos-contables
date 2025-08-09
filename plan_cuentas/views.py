from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db import transaction, IntegrityError
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from .models import PlanCuenta, Cuenta
from .forms import PlanCuentaForm, CuentaForm
from empresas.models import Empresa
import logging

logger = logging.getLogger(__name__)

@login_required
def plan_cuenta_list(request):
    """Lista todos los planes de cuentas disponibles"""
    try:
        # Obtener parámetros de filtrado
        search = request.GET.get('search', '')
        empresa = request.GET.get('empresa', '')
        
        # Query base para planes de cuentas
        planes = PlanCuenta.objects.select_related('perfil').all()
        
        # Aplicar filtros
        if search:
            planes = planes.filter(descripcion__icontains=search)
            
        if empresa:
            planes = planes.filter(empresa=empresa)
        
        # Ordenar por empresa y descripción
        planes = planes.order_by('empresa', 'descripcion')
        
        # Estadísticas
        stats = {
            'total_planes': planes.count(),
            'total_cuentas': Cuenta.objects.count(),
            'empresas_stats': planes.select_related('empresa').values(
                'empresa__id', 'empresa__nombre'
            ).annotate(count=Count('id')).distinct(),
        }
        
        # Paginación
        paginator = Paginator(planes, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'planes': page_obj,
            'stats': stats,
            'search': search,
            'empresa_filter': empresa,
        }
        
        return render(request, 'plan_cuentas/list_new.html', context)
        
    except Exception as e:
        logger.error(f"Error al cargar los planes de cuentas: {e}")
        messages.error(request, "Error al cargar los planes de cuentas")
        return render(request, 'plan_cuentas/list_new.html', {'planes': []})


@login_required
def cuenta_list(request):
    """Lista todas las cuentas contables simplificadas"""
    try:
        # Obtener parámetros de filtrado
        search = request.GET.get('search', '')
        
        # Query base
        cuentas = Cuenta.objects.all()
        
        # Aplicar filtros
        if search:
            cuentas = cuentas.filter(
                Q(cuenta__icontains=search) |
                Q(descripcion__icontains=search)
            )
        
        # Ordenar por ID
        cuentas = cuentas.order_by('id')
        
        # Estadísticas
        cuentas_con_descripcion = cuentas.exclude(descripcion__isnull=True).exclude(descripcion='').count()
        
        context = {
            'cuentas': cuentas,
            'cuentas_con_descripcion': cuentas_con_descripcion,
            'search': search,
        }
        
        return render(request, 'plan_cuentas/cuenta_list.html', context)
        
    except Exception as e:
        logger.error(f"Error al cargar las cuentas contables: {e}")
        messages.error(request, "Error al cargar las cuentas contables")
        return render(request, 'plan_cuentas/cuenta_list.html', {'cuentas': []})

@login_required
def plan_cuenta_create(request):
    """Crear un nuevo plan de cuentas"""
    if request.method == 'POST':
        form = PlanCuentaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    plan = form.save()
                    
                messages.success(
                    request, 
                    f'Plan de cuentas "{plan.descripcion}" creado exitosamente'
                )
                return redirect('plan_cuentas:plan_cuenta_list')
                
            except IntegrityError as e:
                logger.error(f"Error de integridad al crear plan de cuentas: {e}")
                messages.error(request, "Error al crear el plan de cuentas")
            except Exception as e:
                logger.error(f"Error al crear plan de cuentas: {e}")
                messages.error(request, "Error interno al crear el plan de cuentas")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario")
    else:
        form = PlanCuentaForm()
    
    context = {
        'form': form,
        'title': 'Crear Plan de Cuentas',
        'button_text': 'Crear Plan'
    }
    
    return render(request, 'plan_cuentas/form.html', context)


@login_required
def cuenta_create(request):
    """Crear una nueva cuenta contable simplificada"""
    if request.method == 'POST':
        form = CuentaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    cuenta = form.save()
                    
                messages.success(
                    request, 
                    f'Cuenta "{cuenta.cuenta} - {cuenta.descripcion}" creada exitosamente'
                )
                return redirect('plan_cuentas:cuenta_list')
                
            except IntegrityError as e:
                logger.error(f"Error de integridad al crear cuenta: {e}")
                messages.error(request, "Ya existe una cuenta con ese nombre")
            except Exception as e:
                logger.error(f"Error al crear cuenta: {e}")
                messages.error(request, "Error interno al crear la cuenta contable")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario")
    else:
        form = CuentaForm()
    
    context = {
        'form': form,
        'title': 'Crear Cuenta Contable',
        'button_text': 'Crear Cuenta'
    }
    return render(request, 'plan_cuentas/cuenta_create.html', context)

@login_required
def plan_cuenta_edit(request, id):
    """Editar un plan de cuentas existente"""
    plan = get_object_or_404(PlanCuenta, id=id)
    
    if request.method == 'POST':
        form = PlanCuentaForm(request.POST, instance=plan)
        if form.is_valid():
            try:
                with transaction.atomic():
                    plan = form.save()
                    
                messages.success(
                    request, 
                    f'Plan de cuentas "{plan.descripcion}" actualizado exitosamente'
                )
                return redirect('plan_cuentas:plan_cuenta_list')
                
            except Exception as e:
                logger.error(f"Error al actualizar plan de cuentas: {e}")
                messages.error(request, "Error interno al actualizar el plan de cuentas")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario")
    else:
        form = PlanCuentaForm(instance=plan)
    
    context = {
        'form': form,
        'title': f'Editar Plan: {plan.descripcion}',
        'button_text': 'Actualizar Plan',
        'plan': plan
    }
    
    return render(request, 'plan_cuentas/form.html', context)


@login_required
def cuenta_edit(request, id):
    """Editar una cuenta contable existente"""
    cuenta = get_object_or_404(Cuenta, id=id)
    
    if request.method == 'POST':
        form = CuentaForm(request.POST, instance=cuenta)
        if form.is_valid():
            try:
                with transaction.atomic():
                    cuenta = form.save()
                    
                messages.success(
                    request, 
                    f'Cuenta {cuenta.cuenta} - {cuenta.descripcion} actualizada exitosamente'
                )
                return redirect('plan_cuentas:cuenta_list')
                
            except Exception as e:
                logger.error(f"Error al actualizar cuenta: {e}")
                messages.error(request, "Error interno al actualizar la cuenta contable")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario")
    else:
        form = CuentaForm(instance=cuenta)
    
    context = {
        'form': form,
        'title': f'Editar Cuenta: {cuenta.cuenta}',
        'button_text': 'Actualizar Cuenta',
        'cuenta': cuenta
    }
    
    return render(request, 'plan_cuentas/cuenta_create.html', context)


@login_required
def plan_cuenta_detail(request, id):
    """Ver detalles de un plan de cuentas"""
    plan = get_object_or_404(PlanCuenta, id=id)
    
    # Obtener cuentas asociadas a este plan
    cuentas_asociadas = Cuenta.objects.filter(plan_cuentas=plan).order_by('cuenta')
    
    # Estadísticas del plan
    stats = {
        'total_cuentas': cuentas_asociadas.count(),
        'cuentas_por_grupo': cuentas_asociadas.values('grupo').annotate(count=Count('id')),
    }
    
    context = {
        'plan': plan,
        'cuentas': cuentas_asociadas,
        'stats': stats,
    }
    
    return render(request, 'plan_cuentas/plan_detail.html', context)


@login_required
def cuenta_detail(request, id):
    """Ver detalles de una cuenta contable"""
    cuenta = get_object_or_404(Cuenta, id=id)
    
    context = {
        'cuenta': cuenta,
    }
    
    return render(request, 'plan_cuentas/cuenta_detail.html', context)


@login_required
def plan_cuenta_delete(request, id):
    """Eliminar un plan de cuentas"""
    plan = get_object_or_404(PlanCuenta, id=id)
    
    if request.method == 'POST':
        try:
            # Verificar si tiene cuentas asociadas
            if Cuenta.objects.filter(plan_cuentas=plan).exists():
                messages.error(
                    request, 
                    f'No se puede eliminar el plan "{plan.descripcion}" porque tiene cuentas asociadas'
                )
                return redirect('plan_cuentas:plan_cuenta_list')
            
            with transaction.atomic():
                plan.delete()
                
            messages.success(request, f'Plan de cuentas "{plan.descripcion}" eliminado exitosamente')
            return redirect('plan_cuentas:plan_cuenta_list')
            
        except Exception as e:
            logger.error(f"Error al eliminar plan de cuentas: {e}")
            messages.error(request, "Error interno al eliminar el plan de cuentas")
            return redirect('plan_cuentas:plan_cuenta_list')
    
    context = {
        'plan': plan,
        'cuentas_count': Cuenta.objects.filter(plan_cuentas=plan).count(),
    }
    
    return render(request, 'plan_cuentas/plan_confirm_delete.html', context)


@login_required
def cuenta_delete(request, id):
    """Eliminar una cuenta contable"""
    cuenta = get_object_or_404(Cuenta, id=id)
    
    if request.method == 'POST':
        try:
            # Verificar si se puede eliminar (agregar validaciones según sea necesario)
            with transaction.atomic():
                cuenta.delete()
                
            messages.success(request, f'Cuenta {cuenta.cuenta} - {cuenta.descripcion} eliminada exitosamente')
            return redirect('plan_cuentas:cuenta_list')
            
        except Exception as e:
            logger.error(f"Error al eliminar cuenta: {e}")
            messages.error(request, "Error interno al eliminar la cuenta contable")
            return redirect('plan_cuentas:cuenta_list')
    
    context = {
        'cuenta': cuenta,
    }
    
    return render(request, 'plan_cuentas/cuenta_confirm_delete.html', context)


@login_required
def get_cuentas_by_empresa(request):
    """Obtener cuentas por empresa vía AJAX"""
    empresa = request.GET.get('empresa')
    if empresa:
        cuentas = PlanCuenta.objects.filter(empresa=empresa).values(
            'id', 'descripcion'
        )
        return JsonResponse(list(cuentas), safe=False)
    return JsonResponse([], safe=False)

@login_required
def cuentas_por_plan_ajax(request, plan_id):
    """Obtener cuentas de un plan específico vía AJAX"""
    try:
        plan = get_object_or_404(PlanCuenta, id=plan_id)
        cuentas = Cuenta.objects.filter(plan_cuentas=plan).values(
            'id', 'cuenta', 'descripcion', 'grupo'
        ).order_by('cuenta')
        return JsonResponse(list(cuentas), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_cuentas_madre_ajax(request):
    """Vista AJAX para obtener cuentas madre disponibles según el plan seleccionado"""
    plan_id = request.GET.get('plan_id')
    cuenta_actual_id = request.GET.get('cuenta_id')  # Para evitar auto-referencias
    
    if not plan_id:
        return JsonResponse({'cuentas': []})
    
    try:
        # Obtener cuentas del plan, excluyendo la cuenta actual si existe
        cuentas_query = Cuenta.objects.filter(plan_cuentas_id=plan_id)
        if cuenta_actual_id:
            cuentas_query = cuentas_query.exclude(id=cuenta_actual_id)
        
        cuentas = cuentas_query.values('id', 'cuenta', 'descripcion').order_by('cuenta')
        
        return JsonResponse({
            'cuentas': list(cuentas)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
