from django.contrib import admin
from .models import Officer

@admin.register(Officer)
class OfficerAdmin(admin.ModelAdmin):
    list_display = ('user', 'designation', 'department', 'employee_id')
    search_fields = ('user__username', 'designation', 'department', 'employee_id')
    list_filter = ('designation', 'department')
    autocomplete_fields = ['user']