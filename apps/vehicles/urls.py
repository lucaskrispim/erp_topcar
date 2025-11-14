from django.urls import path
from . import views

urlpatterns = [
    path('', views.vehicle_list, name='vehicle_list'),
    path('add/', views.vehicle_create, name='vehicle_create'), # Nova rota
    path('<int:pk>/edit/', views.vehicle_update, name='vehicle_update'),
    path('<int:pk>/delete/', views.vehicle_delete, name='vehicle_delete'),
    path('reports/roi/', views.vehicle_roi_report, name='vehicle_roi_report'),
]