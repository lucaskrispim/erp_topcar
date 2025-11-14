from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Entity
from .forms import EntityForm

@login_required
def entity_list(request):
    query = request.GET.get('q', '')
    entities = Entity.objects.all().order_by('nome_razao_social')

    if query:
        entities = entities.filter(
            Q(nome_razao_social__icontains=query) |
            Q(documento_principal__icontains=query)
        )

    return render(request, 'parties/entity_list.html', {'entities': entities})

@login_required
def entity_create(request):
    if request.method == 'POST':
        form = EntityForm(request.POST)
        if form.is_valid():
            entity = form.save(commit=False)
            entity.created_by = request.user
            entity.save()
            messages.success(request, f"Entidade '{entity.nome_razao_social}' criada com sucesso.")
            return redirect('entity_list')
    else:
        form = EntityForm()
    
    return render(request, 'parties/entity_form.html', {'form': form, 'action': 'Criar'})

@login_required
def entity_update(request, pk):
    entity = get_object_or_404(Entity, pk=pk)
    if request.method == 'POST':
        form = EntityForm(request.POST, instance=entity)
        if form.is_valid():
            form.save()
            messages.success(request, f"Entidade '{entity.nome_razao_social}' atualizada.")
            return redirect('entity_list')
    else:
        form = EntityForm(instance=entity)

    return render(request, 'parties/entity_form.html', {'form': form, 'action': 'Editar'})