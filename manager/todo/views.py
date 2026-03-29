from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from .models import Task, Schedule
from .forms import TaskForm, ScheduleForm
import calendar
import json
from datetime import date
from collections import defaultdict
from django.views.decorators.cache import never_cache


# ─── Dashboard ────────────────────────────────────────────────────────────────

# Add these imports at the top of todo/views.py
@never_cache
@login_required
def dashboard(request):
    today = date.today()

    all_tasks       = Task.objects.filter(user=request.user)
    pending_tasks   = all_tasks.filter(is_completed=False)
    completed_tasks = all_tasks.filter(is_completed=True)
    total           = all_tasks.count()
    done            = completed_tasks.count()
    progress        = round((done / total) * 100) if total > 0 else 0

    today_count         = pending_tasks.filter(due_date=today).count()
    overdue_count       = pending_tasks.filter(due_date__lt=today).count()
    high_priority_count = pending_tasks.filter(priority='high').count()

    high_count   = all_tasks.filter(priority='high').count()
    medium_count = all_tasks.filter(priority='medium').count()
    low_count    = all_tasks.filter(priority='low').count()

    # Category counts for chart
    cat_work     = all_tasks.filter(category='work').count()
    cat_personal = all_tasks.filter(category='personal').count()
    cat_school   = all_tasks.filter(category='school').count()
    cat_health   = all_tasks.filter(category='health').count()
    cat_finance  = all_tasks.filter(category='finance').count()
    cat_other    = all_tasks.filter(category='other').count()

    upcoming_schedules = Schedule.objects.filter(
        user=request.user, is_completed=False, date__gte=today,
    ).order_by('date', 'start_time')[:5]

    upcoming_schedules_count = Schedule.objects.filter(
        user=request.user, is_completed=False, date__gte=today,
    ).count()

    # Habits snapshot
    habit_streaks = []
    total_habits  = 0
    try:
        from habits.models import Habit
        habits       = Habit.objects.filter(user=request.user, is_archived=False).prefetch_related('logs')
        total_habits = habits.count()
        monday       = today - timedelta(days=today.weekday())
        week         = [monday + timedelta(days=i) for i in range(7)]
        COLOR_MAP    = {
            'blue': '#3b82f6', 'green': '#22c55e', 'purple': '#a855f7',
            'red':  '#ef4444', 'amber': '#f59e0b', 'pink':   '#ec4899',
        }
        for habit in habits[:5]:
            logged = set(habit.logs.filter(completed=True).values_list('date', flat=True))
            habit_streaks.append({
                'name':           habit.name,
                'icon':           habit.icon,
                'frequency':      habit.get_frequency_display(),
                'current_streak': habit.current_streak,
                'week_cells':     [
                    COLOR_MAP.get(habit.color, '#3b82f6') if d in logged else '#f1f5f9'
                    for d in week
                ],
            })
    except Exception:
        pass

    # Notes snapshot
    recent_notes = []
    total_notes  = 0
    try:
        from notes.models import Note
        recent_notes = list(Note.objects.filter(user=request.user, is_archived=False).order_by('-is_pinned', '-updated_at')[:4])
        total_notes  = Note.objects.filter(user=request.user, is_archived=False).count()
    except Exception:
        pass

    return render(request, 'dashboard/dashboard.html', {
        'pending_tasks':            pending_tasks,
        'completed_tasks':          completed_tasks,
        'upcoming_schedules':       upcoming_schedules,
        'upcoming_schedules_count': upcoming_schedules_count,
        'total':                    total,
        'done':                     done,
        'progress':                 progress,
        'today_count':              today_count,
        'overdue_count':            overdue_count,
        'high_priority_count':      high_priority_count,
        'high_count':               high_count,
        'medium_count':             medium_count,
        'low_count':                low_count,
        'cat_work':                 cat_work,
        'cat_personal':             cat_personal,
        'cat_school':               cat_school,
        'cat_health':               cat_health,
        'cat_finance':              cat_finance,
        'cat_other':                cat_other,
        'habit_streaks':            habit_streaks,
        'recent_notes':             recent_notes,
        'total_habits':             total_habits,
        'total_notes':              total_notes,
    })

# ─── Task CRUD ────────────────────────────────────────────────────────────────
@never_cache
@login_required
@require_POST
def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.is_completed = not task.is_completed
    task.save()
    return redirect('dashboard')

@never_cache
@login_required
def update_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = TaskForm(instance=task)
    return render(request, 'todo/update_task.html', {'form': form, 'task': task})

@never_cache
@login_required
@require_POST
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return redirect('dashboard')

@never_cache
@login_required
def todo_list_view(request):
    today    = date.today()
    status   = request.GET.get('status',   'all')
    priority = request.GET.get('priority', 'all')
    category = request.GET.get('category', 'all')

    tasks = Task.objects.filter(user=request.user)
    if status   == 'pending': tasks = tasks.filter(is_completed=False)
    elif status == 'done':    tasks = tasks.filter(is_completed=True)
    if priority != 'all':     tasks = tasks.filter(priority=priority)
    if category != 'all':     tasks = tasks.filter(category=category)

    task_list = list(tasks)
    for task in task_list:
        task.is_overdue = (
            not task.is_completed
            and task.due_date is not None
            and task.due_date < today
        )

    all_tasks    = Task.objects.filter(user=request.user)
    stat_total   = all_tasks.count()
    stat_pending = all_tasks.filter(is_completed=False).count()
    stat_done    = all_tasks.filter(is_completed=True).count()
    stat_overdue = sum(
        1 for t in all_tasks
        if not t.is_completed and t.due_date and t.due_date < today
    )

    return render(request, 'dashboard/todo_list.html', {
        'tasks':            task_list,
        'current_status':   status,
        'current_priority': priority,
        'current_category': category,
        'stat_total':       stat_total,
        'stat_pending':     stat_pending,
        'stat_done':        stat_done,
        'stat_overdue':     stat_overdue,
    })


# ─── Calendar ─────────────────────────────────────────────────────────────────

def _calendar_redirect(task):
    """Redirect back to the calendar month the task belongs to."""
    if task.due_date:
        url = reverse('calendar') + f'?year={task.due_date.year}&month={task.due_date.month}'
    else:
        url = reverse('calendar')
    return redirect(url)

@never_cache
@login_required
def calendar_view(request):
    today = date.today()
    year  = int(request.GET.get('year',  today.year))
    month = int(request.GET.get('month', today.month))

    prev_year,  prev_month  = (year - 1, 12) if month == 1  else (year, month - 1)
    next_year,  next_month  = (year + 1, 1)  if month == 12 else (year, month + 1)

    month_tasks = Task.objects.filter(
        user=request.user, due_date__year=year, due_date__month=month
    )
    tasks_by_day = {}
    for task in month_tasks:
        tasks_by_day.setdefault(task.due_date.day, []).append(task)

    month_schedules = Schedule.objects.filter(
        user=request.user, date__year=year, date__month=month
    )
    schedules_by_day = {}
    for s in month_schedules:
        schedules_by_day.setdefault(s.date.day, []).append(s)

    CATEGORY_META = {
        'work':     {'label': 'Work',     'dot': 'bg-blue-400'},
        'personal': {'label': 'Personal', 'dot': 'bg-purple-400'},
        'school':   {'label': 'School',   'dot': 'bg-indigo-400'},
        'health':   {'label': 'Health',   'dot': 'bg-green-400'},
        'finance':  {'label': 'Finance',  'dot': 'bg-yellow-400'},
        'other':    {'label': 'Other',    'dot': 'bg-slate-400'},
    }

    tasks_by_category = defaultdict(list)
    for task in month_tasks:
        tasks_by_category[task.category].append(task)

    schedule_groups = []
    for cat_key, meta in CATEGORY_META.items():
        tasks = tasks_by_category.get(cat_key, [])
        if tasks:
            schedule_groups.append({
                'key':   cat_key,
                'label': meta['label'],
                'dot':   meta['dot'],
                'tasks': tasks,
                'total': len(tasks),
                'done':  sum(1 for t in tasks if t.is_completed),
            })

    cal        = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)

    calendar_cells = []
    for week in month_days:
        for day in week:
            cell_tasks     = tasks_by_day.get(day, [])
            cell_schedules = schedules_by_day.get(day, [])
            calendar_cells.append({
                'day':        day,
                'tasks':      cell_tasks,
                'schedules':  cell_schedules,
                'has_items':  bool(cell_tasks or cell_schedules),
                'is_today':   (day != 0 and date(year, month, day) == today),
                'tasks_json': json.dumps(
                    [
                        {
                            'id':           t.id,
                            'title':        t.title,
                            'priority':     t.priority,
                            'category':     t.category,
                            'is_completed': t.is_completed,
                            'type':         'task',
                        }
                        for t in cell_tasks
                    ] + [
                        {
                            'id':           s.id,
                            'title':        s.title,
                            'priority':     s.priority,
                            'category':     s.category,
                            'is_completed': s.is_completed,
                            'start_time':   s.start_time.strftime('%I:%M %p') if s.start_time else None,
                            'type':         'schedule',
                        }
                        for s in cell_schedules
                    ]
                ),
            })

    return render(request, 'dashboard/calendar_view.html', {
        'calendar_cells':  calendar_cells,
        'month_tasks':     list(month_tasks),
        'month_schedules': list(month_schedules),
        'schedule_groups': schedule_groups,
        'day_names':       ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        'month_name':      calendar.month_name[month],
        'year': year, 'month': month,
        'prev_year': prev_year, 'prev_month': prev_month,
        'next_year': next_year, 'next_month': next_month,
    })

@never_cache
@login_required
def calendar_add_task(request):
    due_date = request.GET.get('date', '')
    year     = request.GET.get('year',  date.today().year)
    month    = request.GET.get('month', date.today().month)

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task      = form.save(commit=False)
            task.user = request.user
            task.save()
            return _calendar_redirect(task)
    else:
        form = TaskForm(initial={'due_date': due_date} if due_date else {})

    return render(request, 'dashboard/calendar_task_form.html', {
        'form': form, 'form_title': 'Add Task',
        'year': year, 'month': month, 'due_date': due_date, 'is_edit': False,
    })

@never_cache
@login_required
def calendar_edit_task(request, task_id):
    task  = get_object_or_404(Task, id=task_id, user=request.user)
    year  = request.GET.get('year',  task.due_date.year  if task.due_date else date.today().year)
    month = request.GET.get('month', task.due_date.month if task.due_date else date.today().month)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            return _calendar_redirect(task)
    else:
        form = TaskForm(instance=task)

    return render(request, 'dashboard/calendar_task_form.html', {
        'form': form, 'form_title': 'Edit Task',
        'task': task, 'year': year, 'month': month, 'is_edit': True,
    })

@never_cache
@login_required
def calendar_delete_task(request, task_id):
    task  = get_object_or_404(Task, id=task_id, user=request.user)
    year  = request.GET.get('year',  task.due_date.year  if task.due_date else date.today().year)
    month = request.GET.get('month', task.due_date.month if task.due_date else date.today().month)

    if request.method == 'POST':
        url = reverse('calendar')
        if task.due_date:
            url += f'?year={task.due_date.year}&month={task.due_date.month}'
        task.delete()
        return redirect(url)

    return render(request, 'dashboard/calendar_delete_task.html', {
        'task': task, 'year': year, 'month': month,
    })


# ─── Schedule CRUD ────────────────────────────────────────────────────────────
@never_cache
@login_required
def schedule_view(request):
    today    = date.today()
    status   = request.GET.get('status',   'all')
    priority = request.GET.get('priority', 'all')
    category = request.GET.get('category', 'all')

    schedules = Schedule.objects.filter(user=request.user).order_by('date', 'start_time')
    if status   == 'pending': schedules = schedules.filter(is_completed=False)
    elif status == 'done':    schedules = schedules.filter(is_completed=True)
    if priority != 'all':     schedules = schedules.filter(priority=priority)
    if category != 'all':     schedules = schedules.filter(category=category)

    schedule_list = list(schedules)
    for s in schedule_list:
        s.is_overdue = not s.is_completed and s.date < today

    all_schedules = Schedule.objects.filter(user=request.user)
    stat_total    = all_schedules.count()
    stat_pending  = all_schedules.filter(is_completed=False).count()
    stat_done     = all_schedules.filter(is_completed=True).count()
    stat_overdue = all_schedules.filter(is_completed=False, date__lt=today).count()

    return render(request, 'dashboard/schedule.html', {
        'schedules':        schedule_list,
        'current_status':   status,
        'current_priority': priority,
        'current_category': category,
        'stat_total':       stat_total,
        'stat_pending':     stat_pending,
        'stat_done':        stat_done,
        'stat_overdue':     stat_overdue,
    })

@never_cache
@login_required
def schedule_add(request):
    date_param = request.GET.get('date', '')
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule      = form.save(commit=False)
            schedule.user = request.user
            schedule.save()
            return redirect('schedule')
    else:
        form = ScheduleForm(initial={'date': date_param} if date_param else {})

    return render(request, 'dashboard/schedule_form.html', {
        'form': form, 'form_title': 'Add Schedule', 'is_edit': False,
    })

@never_cache
@login_required
def schedule_edit(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            return redirect('schedule')
    else:
        form = ScheduleForm(instance=schedule)

    return render(request, 'dashboard/schedule_form.html', {
        'form': form, 'form_title': 'Edit Schedule',
        'schedule': schedule, 'is_edit': True,
    })

@never_cache
@login_required
def schedule_delete(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)
    if request.method == 'POST':
        schedule.delete()
        return redirect('schedule')
    return render(request, 'dashboard/schedule_delete.html', {'schedule': schedule})

@never_cache
@login_required
@require_POST
def schedule_toggle(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)
    schedule.is_completed = not schedule.is_completed
    schedule.save()
    return redirect('schedule')