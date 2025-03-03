from django.db import models
from accounts.models import User


class Officer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='officer')
    designation = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.designation})"

