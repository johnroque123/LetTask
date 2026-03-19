from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import random
import string
from django.utils import timezone
from datetime import timedelta
import os


class User(AbstractUser):
    def __str__(self):
        return self.email


def avatar_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'avatars/{instance.user.pk}.{ext}'


class Profile(models.Model):
    user   = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to=avatar_upload_path, blank=True, null=True)
    bio    = models.TextField(max_length=300, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None


class OTPToken(models.Model):
    PURPOSE_VERIFY  = 'verify'
    PURPOSE_RESET   = 'reset'
    PURPOSE_CHOICES = [
        (PURPOSE_VERIFY, 'Account Verification'),
        (PURPOSE_RESET,  'Password Reset'),
    ]

    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='otp_tokens')
    code       = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)
    purpose    = models.CharField(max_length=10, choices=PURPOSE_CHOICES, default=PURPOSE_VERIFY)

    OTP_EXPIRY_MINUTES = 5

    @staticmethod
    def generate_code():
        return ''.join(random.choices(string.digits, k=6))

    def is_valid(self):
        expiry = self.created_at + timedelta(minutes=self.OTP_EXPIRY_MINUTES)
        return not self.is_used and timezone.now() < expiry

    def __str__(self):
        return f"OTP for {self.user.username} ({self.purpose}, {'used' if self.is_used else 'active'})"
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'code', 'is_used']),
        ]