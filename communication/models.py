from django.db import models
from accounts.models import User


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_announcement = models.BooleanField(default=False)  # True for announcement, False for direct message
    
    def __str__(self):
        return f"Message from {self.sender} to {self.receiver} at {self.timestamp}"
