from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Registra o CustomUser usando a classe base do Django para manter a UI de senha/perms
admin.site.register(CustomUser, UserAdmin)
