from django.shortcuts import render
from django.db.models import Sum
from vehicles.models import Vehicle
from financial.models import Ledger
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    # Estatísticas rápidas para o topo da tela
    total_carros = Vehicle.objects.count()
    carros_disponiveis = Vehicle.objects.filter(status='AVAILABLE').count()
    
    # Soma do dinheiro "Na Rua" (A receber)
    a_receber = Ledger.objects.filter(
        transaction_type='RECEIVABLE', 
        status='OPEN'
    ).aggregate(total=Sum('total_value'))['total'] or 0

    context = {
        'total_carros': total_carros,
        'carros_disponiveis': carros_disponiveis,
        'a_receber': a_receber,
    }
    return render(request, 'core/dashboard.html', context)