import json
import base64
import uuid

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.core.files.base import ContentFile

from .models import Note


MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


# =========================
# HELPERS
# =========================
def _save_image_from_b64(b64_data_uri):
    """
    Convert base64 image (data URI) into Django file.
    """
    try:
        header, data = b64_data_uri.split(',', 1)

        mime = header.split(':')[1].split(';')[0]  # image/jpeg
        ext  = mime.split('/')[1]                  # jpeg

        if ext == 'jpeg':
            ext = 'jpg'

        raw = base64.b64decode(data)

        if len(raw) > MAX_IMAGE_BYTES:
            return None, 'too_large'

        filename = f"note_{uuid.uuid4().hex}.{ext}"
        return ContentFile(raw, name=filename), None

    except Exception:
        return None, 'invalid'


# =========================
# VIEWS
# =========================
@never_cache
@login_required
def notes_view(request):
    notes = Note.objects.filter(user=request.user, is_archived=False)

    return render(request, 'notes/notes.html', {
        'pinned': notes.filter(is_pinned=True),
        'others': notes.filter(is_pinned=False),
        'total': notes.count(),
    })


@never_cache
@login_required
def archived_notes_view(request):
    notes = Note.objects.filter(user=request.user, is_archived=True).order_by('-updated_at')

    return render(request, 'notes/archived_notes.html', {
        'archived': notes,
        'total': notes.count(),
    })


# =========================
# CREATE
# =========================
@never_cache
@login_required
@require_POST
def note_create(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    title   = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    color   = data.get('color', 'yellow')
    mode    = data.get('mode', 'text')
    b64_img = data.get('image')

    # ✅ validation
    if not content:
        return JsonResponse({
            'ok': False,
            'errors': {'content': ['This field is required.']}
        }, status=400)

    note = Note(
        user=request.user,
        title=title,
        content=content,
        color=color,
        mode=mode
    )

    # image
    if b64_img:
        file, err = _save_image_from_b64(b64_img)

        if err == 'too_large':
            return JsonResponse({'ok': False, 'error': 'Image exceeds 5 MB.'}, status=400)

        if err == 'invalid':
            return JsonResponse({'ok': False, 'error': 'Invalid image format.'}, status=400)

        if file:
            note.image.save(file.name, file, save=False)

    note.save()

    return JsonResponse({
        'ok': True,
        'id': note.pk,
        'title': note.title,
        'content': note.content,
        'color': note.color,
        'mode': note.mode,
        'is_pinned': note.is_pinned,
        'image_url': note.image.url if note.image else '',
        'updated': note.updated_at.strftime('%b %d, %Y'),
    })


# =========================
# UPDATE
# =========================
@never_cache
@login_required
@require_POST
def note_update(request, note_id):
    note = get_object_or_404(Note, pk=note_id, user=request.user)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    title   = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()

    # ✅ validation (fixes 400 issue properly)
    if not content:
        return JsonResponse({
            'ok': False,
            'errors': {'content': ['This field is required.']}
        }, status=400)

    note.title = title
    note.content = content
    note.color = data.get('color', note.color)
    note.mode  = data.get('mode', note.mode)

    # ── IMAGE HANDLING ──

    # remove image
    if data.get('remove_image') and note.image:
        note.image.delete(save=False)
        note.image = None

    # new image
    b64_img = data.get('image')
    if b64_img:
        if note.image:
            note.image.delete(save=False)

        file, err = _save_image_from_b64(b64_img)

        if err == 'too_large':
            return JsonResponse({'ok': False, 'error': 'Image exceeds 5 MB.'}, status=400)

        if err == 'invalid':
            return JsonResponse({'ok': False, 'error': 'Invalid image format.'}, status=400)

        if file:
            note.image.save(file.name, file, save=False)

    # ✅ safe save
    note.save()

    return JsonResponse({
        'ok': True,
        'image_url': note.image.url if note.image else '',
        'updated': note.updated_at.strftime('%b %d, %Y'),
    })


# =========================
# DELETE
# =========================
@never_cache
@login_required
@require_POST
def note_delete(request, note_id):
    note = get_object_or_404(Note, pk=note_id, user=request.user)

    if note.image:
        note.image.delete(save=False)

    note.delete()

    return JsonResponse({'ok': True})


# =========================
# PIN
# =========================
@never_cache
@login_required
@require_POST
def note_toggle_pin(request, note_id):
    note = get_object_or_404(Note, pk=note_id, user=request.user)

    note.is_pinned = not note.is_pinned
    note.save(update_fields=['is_pinned'])

    return JsonResponse({
        'ok': True,
        'is_pinned': note.is_pinned
    })


# =========================
# ARCHIVE
# =========================
@never_cache
@login_required
@require_POST
def note_toggle_archive(request, note_id):
    note = get_object_or_404(Note, pk=note_id, user=request.user)

    note.is_archived = not note.is_archived

    if note.is_archived:
        note.is_pinned = False

    note.save(update_fields=['is_archived', 'is_pinned'])

    return JsonResponse({
        'ok': True,
        'is_archived': note.is_archived
    })