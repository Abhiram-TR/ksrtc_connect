from django.contrib import admin
from .models import Schedule

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'depot', 'created_at', 'is_global', 'has_pdf')
    list_filter = ('is_global', 'created_at')
    search_fields = ('title', 'description', 'created_by__username', 'depot__name')
    date_hierarchy = 'created_at'
    
    def has_pdf(self, obj):
        return bool(obj.pdf_file)
    
    has_pdf.boolean = True
    has_pdf.short_description = 'PDF Attached'