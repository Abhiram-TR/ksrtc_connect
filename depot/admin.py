from django.contrib import admin
from .models import Depot

@admin.register(Depot)
class DepotAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'contact_person', 'user', 'is_active', 'created_at')
    list_filter = ('is_active', 'location')
    search_fields = ('name', 'location', 'address', 'contact_person', 'user__username')
    date_hierarchy = 'created_at'
    autocomplete_fields = ['user']