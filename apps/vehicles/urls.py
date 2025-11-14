from django.urls import path
from . import views

urlpatterns = [
    path('', views.vehicle_list, name='vehicle_list'),
    path('add/', views.vehicle_create, name='vehicle_create'), # Nova rota
    path('<int:pk>/edit/', views.vehicle_update, name='vehicle_update'),
    path('<int:pk>/delete/', views.vehicle_delete, name='vehicle_delete'),
    path('reports/roi/', views.vehicle_roi_report, name='vehicle_roi_report'),

    path('ajax/load-models/', views.load_models, name='load_models'),

    path('brands/', views.brand_list, name='brand_list'),
    path('brands/new/', views.brand_create, name='brand_create'),
    path('brands/<int:pk>/edit/', views.brand_update, name='brand_update'),
    path('brands/<int:pk>/delete/', views.brand_delete, name='brand_delete'),

    # --- NOVAS ROTAS DE MODELOS ---
    path('models/', views.model_list, name='model_list'),
    path('models/new/', views.model_create, name='model_create'),
    path('models/<int:pk>/edit/', views.model_update, name='model_update'),
    path('models/<int:pk>/delete/', views.model_delete, name='model_delete'),
]