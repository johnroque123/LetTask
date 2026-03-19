from django.db import models
from django.conf import settings


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low',    'Low'),
        ('medium', 'Medium'),
        ('high',   'High'),
    ]
    CATEGORY_CHOICES = [
        ('work',     'Work'),
        ('personal', 'Personal'),
        ('school',   'School'),
        ('health',   'Health'),
        ('finance',  'Finance'),
        ('other',    'Other'),
    ]

    user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title        = models.CharField(max_length=255)
    priority     = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    category     = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    due_date     = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = [
            models.Case(
                models.When(priority='high',   then=0),
                models.When(priority='medium', then=1),
                models.When(priority='low',    then=2),
                default=3,
                output_field=models.IntegerField(),
            ),
            'due_date',
            '-created_at',
        ]

    def __str__(self):
        return self.title


class Schedule(models.Model):
    PRIORITY_CHOICES = [
        ('low',    'Low'),
        ('medium', 'Medium'),
        ('high',   'High'),
    ]
    CATEGORY_CHOICES = [
        ('work',     'Work'),
        ('personal', 'Personal'),
        ('school',   'School'),
        ('health',   'Health'),
        ('finance',  'Finance'),
        ('other',    'Other'),
    ]
    REPEAT_CHOICES = [
        ('none',    'No Repeat'),
        ('daily',   'Daily'),
        ('weekly',  'Weekly'),
        ('monthly', 'Monthly'),
    ]

    user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title        = models.CharField(max_length=255)
    description  = models.TextField(blank=True, default='')
    priority     = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    category     = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    date         = models.DateField()
    start_time   = models.TimeField(null=True, blank=True)
    end_time     = models.TimeField(null=True, blank=True)
    repeat       = models.CharField(max_length=10, choices=REPEAT_CHOICES, default='none')
    is_completed = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.title} ({self.date})"

    @property
    def duration_display(self):
        if self.start_time and self.end_time:
            return f"{self.start_time.strftime('%I:%M %p')} – {self.end_time.strftime('%I:%M %p')}"
        elif self.start_time:
            return self.start_time.strftime('%I:%M %p')
        return None