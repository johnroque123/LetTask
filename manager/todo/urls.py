# dashboard/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ─── Dashboard ─────────────────────────────
    path('dashboard/', views.dashboard, name='dashboard'),

    # ─── Task CRUD ────────────────────────────
    path('tasks/', views.todo_list_view, name='todo_list'),
    path('tasks/<int:task_id>/update/', views.update_task, name='update_task'),
    path('tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    path('tasks/<int:task_id>/toggle/', views.toggle_task, name='toggle_task'),

    # ─── Calendar ─────────────────────────────
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/add-task/', views.calendar_add_task, name='calendar_add_task'),
    path('calendar/edit-task/<int:task_id>/', views.calendar_edit_task, name='calendar_edit_task'),
    path('calendar/delete-task/<int:task_id>/', views.calendar_delete_task, name='calendar_delete_task'),

    # ─── Schedule CRUD ────────────────────────
    path('schedule/', views.schedule_view, name='schedule'),
    path('schedule/add/', views.schedule_add, name='schedule_add'),
    path('schedule/edit/<int:schedule_id>/', views.schedule_edit, name='schedule_edit'),
    path('schedule/delete/<int:schedule_id>/', views.schedule_delete, name='schedule_delete'),
    path('schedule/toggle/<int:schedule_id>/', views.schedule_toggle, name='schedule_toggle'),
]