from django.db import models
from accounts.models import User


class Depot(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='depot')
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    address = models.TextField()
    contact_person = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

