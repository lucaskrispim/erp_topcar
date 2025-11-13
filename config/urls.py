"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
# 1. Adicione 'include' aqui na importação
from django.urls import path, include 

# 2. Importe a view do Dashboard que criamos no Passo 7
from core.views import dashboard 

urlpatterns = [
    path('admin/', admin.site.urls),

    # 1. Adicione as rotas de autenticação padrão do Django
    # Isso cria rotas mágicas como: /accounts/login/ e /accounts/logout/
    path('accounts/', include('django.contrib.auth.urls')),

    # 3. Rota da Página Inicial (Dashboard)
    # Quando acessar http://localhost:8000/, chama o dashboard
    path('', dashboard, name='dashboard'),

    # 4. Rota do App de Veículos
    # Quando acessar http://localhost:8000/vehicles/..., manda para o arquivo vehicles/urls.py
    path('vehicles/', include('vehicles.urls')),
]
