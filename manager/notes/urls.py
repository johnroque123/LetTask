from django.urls import path
from . import views

urlpatterns = [
    path('',                            views.notes_view,        name='notes'),
    path('create/',                     views.note_create,       name='note_create'),
    path('<int:note_id>/update/',       views.note_update,       name='note_update'),
    path('<int:note_id>/delete/',       views.note_delete,       name='note_delete'),
    path('<int:note_id>/pin/',          views.note_toggle_pin,   name='note_toggle_pin'),
    path('<int:note_id>/archive/',      views.note_toggle_archive, name='note_archive'),
    path('archived/',                   views.archived_notes_view, name='notes_archived'),
]