from django import forms
from .models import Task, Schedule

INPUT_CLASS    = "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
SELECT_CLASS   = "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
TEXTAREA_CLASS = "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"


class TaskForm(forms.ModelForm):
    class Meta:
        model  = Task
        fields = ['title', 'priority', 'category', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Task title...',
            }),
            'priority': forms.Select(attrs={'class': SELECT_CLASS}),
            'category': forms.Select(attrs={'class': SELECT_CLASS}),
            'due_date': forms.DateInput(attrs={
                'class': INPUT_CLASS,
                'type': 'date',
            }),
        }


class ScheduleForm(forms.ModelForm):
    class Meta:
        model  = Schedule
        fields = ['title', 'description', 'priority', 'category', 'date', 'start_time', 'end_time', 'repeat']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Schedule title...',
            }),
            'description': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'placeholder': 'Optional notes...',
                'rows': 2,
            }),
            'priority':   forms.Select(attrs={'class': SELECT_CLASS}),
            'category':   forms.Select(attrs={'class': SELECT_CLASS}),
            'date': forms.DateInput(attrs={
                'class': INPUT_CLASS,
                'type': 'date',
            }),
            'start_time': forms.TimeInput(attrs={
                'class': INPUT_CLASS,
                'type': 'time',
            }),
            'end_time': forms.TimeInput(attrs={
                'class': INPUT_CLASS,
                'type': 'time',
            }),
            'repeat': forms.Select(attrs={'class': SELECT_CLASS}),
        }