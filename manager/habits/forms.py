from django import forms
from .models import Habit

INPUT_CLASS  = "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
SELECT_CLASS = "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"


class HabitForm(forms.ModelForm):
    class Meta:
        model  = Habit
        fields = ['name', 'description', 'frequency', 'color', 'icon', 'target_days']
        widgets = {
            'name': forms.TextInput(attrs={
                'class':       INPUT_CLASS,
                'placeholder': 'e.g. Morning run, Read 30 mins…',
            }),
            'description': forms.Textarea(attrs={
                'class':       INPUT_CLASS + ' resize-none',
                'placeholder': 'Optional description…',
                'rows':        2,
            }),
            'frequency':   forms.Select(attrs={'class': SELECT_CLASS}),
            'color':       forms.Select(attrs={'class': SELECT_CLASS}),
            'icon': forms.TextInput(attrs={
                'class':       INPUT_CLASS,
                'placeholder': 'Single emoji e.g. 🏃',
                'maxlength':   '10',
            }),
            'target_days': forms.NumberInput(attrs={
                'class': INPUT_CLASS,
                'min':   '1',
                'max':   '365',
            }),
        }