from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json

from .models import Note
from .forms import NoteForm


@login_required
def notes_view(request):
    notes  = Note.objects.filter(user=request.user)
    pinned = notes.filter(is_pinned=True)
    others = notes.filter(is_pinned=False)
    form   = NoteForm()
    return render(request, 'notes/notes.html', {
        'pinned': pinned,
        'others': others,
        'form':   form,
        'total':  notes.count(),
    })


@login_required
@require_POST
def note_create(request):
    form = NoteForm(request.POST)
    if form.is_valid():
        note      = form.save(commit=False)
        note.user = request.user
        note.save()
        return JsonResponse({
            'ok':       True,
            'id':       note.pk,
            'title':    note.title,
            'content':  note.content,
            'color':    note.color,
            'is_pinned': note.is_pinned,
            'updated':  note.updated_at.strftime('%b %d, %Y'),
        })
    return JsonResponse({'ok': False, 'errors': form.errors}, status=400)


@login_required
@require_POST
def note_update(request, note_id):
    note = get_object_or_404(Note, pk=note_id, user=request.user)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    note.title   = data.get('title', note.title)
    note.content = data.get('content', note.content)
    note.color   = data.get('color', note.color)
    note.save(update_fields=['title', 'content', 'color', 'updated_at'])

    return JsonResponse({
        'ok':      True,
        'updated': note.updated_at.strftime('%b %d, %Y'),
    })

@login_required
@require_POST
def note_delete(request, note_id):
    note = get_object_or_404(Note, pk=note_id, user=request.user)
    note.delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def note_toggle_pin(request, note_id):
    note           = get_object_or_404(Note, pk=note_id, user=request.user)
    note.is_pinned = not note.is_pinned
    note.save(update_fields=['is_pinned'])
    return JsonResponse({'ok': True, 'is_pinned': note.is_pinned})