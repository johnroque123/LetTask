from django.db import models
from django.conf import settings


class Note(models.Model):
    COLOR_CHOICES = [
        ('yellow', 'Yellow'),
        ('blue',   'Blue'),
        ('green',  'Green'),
        ('pink',   'Pink'),
        ('purple', 'Purple'),
        ('white',  'White'),
    ]

    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notes')
    title      = models.CharField(max_length=255, blank=True)
    content    = models.TextField()
    color      = models.CharField(max_length=10, choices=COLOR_CHOICES, default='yellow')
    is_pinned  = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_pinned', '-updated_at']
        indexes  = [
            models.Index(fields=['user', '-is_pinned', '-updated_at']),
        ]

    def __str__(self):
        return self.title or f"Note {self.pk}"