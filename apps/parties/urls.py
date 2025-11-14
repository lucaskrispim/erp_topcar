from django.urls import path
from . import views

urlpatterns = [
    path('', views.entity_list, name='entity_list'),
    path('new/', views.entity_create, name='entity_create'),
    path('<int:pk>/edit/', views.entity_update, name='entity_update'),
]