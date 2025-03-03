from django.contrib import admin
from .models import Announcement

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'priority', 'created_at', 'is_active')
    list_filter = ('priority', 'is_active', 'created_at')
    search_fields = ('title', 'content', 'created_by__username')
    date_hierarchy = 'created_at'
    list_editable = ('priority', 'is_active')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'created_by')
        }),
        ('Settings', {
            'fields': ('priority', 'is_active')
        }),
    )