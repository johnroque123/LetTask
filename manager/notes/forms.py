from django import forms
from .models import Note

INPUT_CLASS    = "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
TEXTAREA_CLASS = "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"


class NoteForm(forms.ModelForm):
    class Meta:
        model  = Note
        fields = ['title', 'content', 'color']
        widgets = {
            'title': forms.TextInput(attrs={
                'class':       INPUT_CLASS,
                'placeholder': 'Title (optional)',
            }),
            'content': forms.Textarea(attrs={
                'class':       TEXTAREA_CLASS,
                'placeholder': 'Write your note...',
                'rows':        5,
            }),
            'color': forms.Select(attrs={
                'class': INPUT_CLASS,
            }),
        }