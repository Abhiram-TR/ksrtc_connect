from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'content_preview', 'timestamp', 'is_read', 'is_announcement')
    list_filter = ('is_read', 'is_announcement', 'timestamp')
    search_fields = ('content', 'sender__username', 'receiver__username')
    date_hierarchy = 'timestamp'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    
    content_preview.short_description = 'Content Preview'