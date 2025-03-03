from django.db import models
from accounts.models import User
from depot.models import Depot


class Schedule(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_schedules')
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name='schedules', null=True, blank=True)
    pdf_file = models.FileField(upload_to='schedules/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_global = models.BooleanField(default=False)  # True if schedule is for all depots
    
    def __str__(self):
        return self.title