from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import Perfil
from .forms import PerfilForm

@login_required
def perfil_list(request):
    perfiles = Perfil.objects.all()
    return render(request, 'perfiles/list.html', {'perfiles': perfiles})

@login_required
def perfil_create(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST)
        if form.is_valid():
            perfil = form.save(commit=False)
            perfil.usuario_creacion = request.user
            perfil.save()
            return redirect('perfiles:perfil_list')
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
    perfil = get_object_or_404(Perfil, pk=id)
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            return redirect('perfiles:perfil_list')
    else:
        form = PerfilForm(instance=perfil)
    
    context = {
        'form': form,
        'id': id,
        'button_text': 'Actualizar'
    }
    return render(request, 'perfiles/form.html', context)

@login_required
def perfil_delete(request, id):
    perfil = get_object_or_404(Perfil, pk=id)
    if request.method == 'POST':
        perfil.delete()
        return redirect('perfiles:perfil_list')
    return render(request, 'perfiles/confirm_delete.html', {'perfil': perfil})
