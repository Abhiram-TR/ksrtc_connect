from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('officer', 'Officer'),
        ('depot', 'Depot'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    last_login_time = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return self.username
