from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import PlanCuenta
from .forms import PlanCuentaForm

@login_required
def plan_cuenta_list(request):
    cuentas = PlanCuenta.objects.all()
    return render(request, 'plan_cuentas/list.html', {'cuentas': cuentas})

@login_required
def plan_cuenta_create(request):
    if request.method == 'POST':
        form = PlanCuentaForm(request.POST)
        if form.is_valid():
            cuenta = form.save(commit=False)
            cuenta.save()
            return redirect('plan_cuentas:plan_cuenta_list')
    else:
        form = PlanCuentaForm()
    
    context = {
        'form': form,
        'id': None,
        'button_text': 'Crear'
    }
    return render(request, 'plan_cuentas/form.html', context)

@login_required
def plan_cuenta_detail(request, id):
    cuenta = get_object_or_404(PlanCuenta, pk=id)
    return render(request, 'plan_cuentas/detail.html', {'cuenta': cuenta})

@login_required
def plan_cuenta_edit(request, id):
    cuenta = get_object_or_404(PlanCuenta, pk=id)
    if request.method == 'POST':
        form = PlanCuentaForm(request.POST, instance=cuenta)
        if form.is_valid():
            form.save()
            return redirect('plan_cuentas:plan_cuenta_list')
    else:
        form = PlanCuentaForm(instance=cuenta)
    
    context = {
        'form': form,
        'id': id,
        'button_text': 'Actualizar'
    }
    return render(request, 'plan_cuentas/form.html', context)

@login_required
def plan_cuenta_delete(request, id):
    cuenta = get_object_or_404(PlanCuenta, pk=id)
    if request.method == 'POST':
        cuenta.delete()
        return redirect('plan_cuentas:plan_cuenta_list')
    return render(request, 'plan_cuentas/confirm_delete.html', {'cuenta': cuenta})
