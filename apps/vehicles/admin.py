from django.contrib import admin
from .models import Brand, Model, Vehicle

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Model)
class ModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand')
    list_filter = ('brand',)
    search_fields = ('name', 'brand__name')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('model', 'plate', 'year_model', 'status', 'sale_price', 'current_owner')
    list_filter = ('status', 'model__brand', 'year_model')
    search_fields = ('chassi', 'plate', 'model__name')
    # Autocomplete para facilitar a busca do dono e do modelo se houverem muitos registros
    autocomplete_fields = ['model', 'current_owner']