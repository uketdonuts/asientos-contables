from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import AccountingEntry
from .forms import AccountingEntryForm

@login_required
def entry_list(request):
    entries = AccountingEntry.objects.filter(asc_user__usr_id=request.user.usr_id)
    return render(request, 'entries/list.html', {'entries': entries})

@login_required
def entry_create(request):
    if request.method == 'POST':
        form = AccountingEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.asc_user_id = request.user.usr_id
            entry.save()
            return redirect('entries:entry_list')  # Use proper namespace
    else:
        form = AccountingEntryForm()
    
    context = {
        'form': form,
        'asc_id': None,  # Indica creación
        'button_text': 'Crear'
    }
    return render(request, 'entries/create.html', context)

@login_required
def entry_edit(request, asc_id):
    entry = get_object_or_404(AccountingEntry, pk=asc_id)
    if request.method == 'POST':
        form = AccountingEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect('entries:entry_list')  # Use proper namespace
    else:
        form = AccountingEntryForm(instance=entry)
    
    context = {
        'form': form,
        'asc_id': asc_id,  # Indica edición
        'button_text': 'Editar'
    }
    return render(request, 'entries/edit.html', context)

@login_required
def entry_delete(request, asc_id):
    entry = get_object_or_404(AccountingEntry, asc_id=asc_id, asc_user_id=request.user.usr_id)
    if request.method == 'POST':
        entry.delete()
        return redirect('entries:entry_list')  # Use proper namespace
    return render(request, 'entries/confirm_delete.html', {'entry': entry})