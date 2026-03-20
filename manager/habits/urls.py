from django.urls import path
from . import views

urlpatterns = [
    path('',                          views.habits_view,   name='habits'),
    path('create/',                   views.habit_create,  name='habit_create'),
    path('<int:habit_id>/toggle/',    views.habit_toggle,  name='habit_toggle'),
    path('<int:habit_id>/delete/',    views.habit_delete,  name='habit_delete'),
    path('<int:habit_id>/archive/',   views.habit_archive, name='habit_archive'),
    path('<int:habit_id>/edit/',      views.habit_edit,    name='habit_edit'),
]