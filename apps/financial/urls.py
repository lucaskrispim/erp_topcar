from django.urls import path
from . import views

urlpatterns = [
    path('', views.financial_list, name='financial_list'),
    path('statement/', views.financial_statement, name='financial_statement'),

    # Rota para o Lançamento Manual
    path('new-manual/', views.ledger_manual_create, name='ledger_manual_create'),

    # --- NOVAS ROTAS DE PLANO DE CONTAS ---
    path('chart-of-accounts/', views.chart_of_accounts_list, name='chart_of_accounts_list'),
    path('chart-of-accounts/new/', views.chart_of_accounts_create, name='chart_of_accounts_create'),
    path('chart-of-accounts/<int:pk>/edit/', views.chart_of_accounts_update, name='chart_of_accounts_update'),
    path('chart-of-accounts/<int:pk>/delete/', views.chart_of_accounts_delete, name='chart_of_accounts_delete'),
]