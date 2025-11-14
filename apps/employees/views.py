from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Employee
from .forms import EmployeeForm

@login_required
def employee_list(request):
    employees = Employee.objects.select_related(
        'entidade', 'usuario_sistema'
    ).order_by('entidade__nome_razao_social')
    
    return render(request, 'employees/employee_list.html', {'employees': employees})

@login_required
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.created_by = request.user
            employee.save()
            messages.success(request, f"Colaborador '{employee.entidade.nome_razao_social}' cadastrado.")
            return redirect('employee_list')
    else:
        form = EmployeeForm()
        
    return render(request, 'employees/employee_form.html', {'form': form, 'action': 'Novo'})

@login_required
def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f"Colaborador '{employee.entidade.nome_razao_social}' atualizado.")
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)
        
    return render(request, 'employees/employee_form.html', {'form': form, 'action': 'Editar'})