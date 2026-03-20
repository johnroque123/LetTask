from django.db import models
from django.conf import settings
from datetime import date, timedelta


class Habit(models.Model):
    FREQUENCY_CHOICES = [
        ('daily',  'Daily'),
        ('weekly', 'Weekly'),
    ]
    COLOR_CHOICES = [
        ('blue',   'Blue'),
        ('green',  'Green'),
        ('purple', 'Purple'),
        ('red',    'Red'),
        ('amber',  'Amber'),
        ('pink',   'Pink'),
    ]

    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='habits')
    name        = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    frequency   = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='daily')
    color       = models.CharField(max_length=10, choices=COLOR_CHOICES, default='blue')
    icon        = models.CharField(max_length=10, blank=True)
    target_days = models.PositiveSmallIntegerField(default=66)
    is_archived = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes  = [
            models.Index(fields=['user', 'is_archived']),
        ]

    def __str__(self):
        return self.name

    @property
    def current_streak(self):
        today      = date.today()
        check      = today
        streak     = 0
        logged     = set(
            self.logs.filter(completed=True).values_list('date', flat=True)
        )
        while check in logged:
            streak += 1
            check  -= timedelta(days=1)
        return streak

    @property
    def longest_streak(self):
        dates = sorted(
            self.logs.filter(completed=True).values_list('date', flat=True)
        )
        if not dates:
            return 0
        longest = current = 1
        for i in range(1, len(dates)):
            if dates[i] - dates[i - 1] == timedelta(days=1):
                current += 1
                longest  = max(longest, current)
            else:
                current = 1
        return longest

    @property
    def completion_rate(self):
        """Percentage of days completed since creation (capped at today)."""
        today      = date.today()
        total_days = (today - self.created_at.date()).days + 1
        if total_days <= 0:
            return 0
        done = self.logs.filter(completed=True).count()
        return min(round((done / total_days) * 100), 100)

    @property
    def total_completions(self):
        return self.logs.filter(completed=True).count()


class HabitLog(models.Model):
    habit     = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='logs')
    date      = models.DateField()
    completed = models.BooleanField(default=True)

    class Meta:
        unique_together = [('habit', 'date')]
        ordering        = ['-date']
        indexes         = [
            models.Index(fields=['habit', 'date']),
        ]

    def __str__(self):
        return f"{self.habit.name} – {self.date}"