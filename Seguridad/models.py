from django.db import models
from django.utils import timezone
from datetime import timedelta

class EmailVerification(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    last_sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['email', '-created_at']),
        ]

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at
