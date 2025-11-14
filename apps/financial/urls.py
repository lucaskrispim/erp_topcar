from django.urls import path
from . import views

urlpatterns = [
    path('', views.financial_list, name='financial_list'),
    path('statement/', views.financial_statement, name='financial_statement'),
]