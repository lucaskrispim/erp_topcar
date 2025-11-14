from django.urls import path
from . import views

urlpatterns = [
    # Listagem (Raiz de sales/)
    path('', views.negotiation_list, name='negotiation_list'),
    
    # Nova Venda
    path('new/', views.negotiation_create, name='negotiation_create'),
    
    # Detalhes (ex: sales/5/)
    path('<int:pk>/', views.negotiation_detail, name='negotiation_detail'),

    path('<int:pk>/cancel/', views.negotiation_cancel, name='negotiation_cancel'),
]