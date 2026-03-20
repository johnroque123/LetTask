from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from datetime import date, timedelta

from .models import Habit, HabitLog
from .forms import HabitForm


def _week_dates():
    """Return list of 7 date objects for Mon–Sun of the current week."""
    today  = date.today()
    monday = today - timedelta(days=today.weekday())
    return [monday + timedelta(days=i) for i in range(7)]


def _heatmap_dates():
    """Return 84 dates (12 weeks) ending today, oldest first."""
    today = date.today()
    return [today - timedelta(days=83 - i) for i in range(84)]


@login_required
def habits_view(request):
    habits     = Habit.objects.filter(user=request.user, is_archived=False).prefetch_related('logs')
    week_dates = _week_dates()
    today      = date.today()

    # Build a set of completed dates per habit for fast lookup
    habit_data = []
    for habit in habits:
        completed_dates = set(
            habit.logs.filter(completed=True).values_list('date', flat=True)
        )
        heatmap = _heatmap_dates()
        habit_data.append({
            'habit':            habit,
            'completed_dates':  completed_dates,
            'week':             [
                {
                    'date':      d,
                    'done':      d in completed_dates,
                    'is_future': d > today,
                }
                for d in week_dates
            ],
            'heatmap': [
                {
                    'date':  d,
                    'done':  d in completed_dates,
                    'label': d.strftime('%b %d'),
                }
                for d in heatmap
            ],
            'current_streak':   habit.current_streak,
            'longest_streak':   habit.longest_streak,
            'completion_rate':  habit.completion_rate,
            'total':            habit.total_completions,
        })

    form = HabitForm()
    return render(request, 'habits/habits.html', {
        'habit_data':  habit_data,
        'week_dates':  week_dates,
        'today':       today,
        'form':        form,
        'total_habits': habits.count(),
    })


@login_required
@require_POST
def habit_create(request):
    form = HabitForm(request.POST)
    if form.is_valid():
        habit      = form.save(commit=False)
        habit.user = request.user
        habit.save()
        messages.success(request, f'Habit "{habit.name}" created.')
    else:
        messages.error(request, 'Please fix the errors below.')
        # Store errors in session to display after redirect
        request.session['habit_form_errors'] = form.errors.as_json()
    return redirect('habits')


@login_required
@require_POST
def habit_toggle(request, habit_id):
    """Toggle a HabitLog entry for a given date. Returns JSON."""
    habit     = get_object_or_404(Habit, pk=habit_id, user=request.user)
    date_str  = request.POST.get('date')

    try:
        log_date = date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'Invalid date'}, status=400)

    if log_date > date.today():
        return JsonResponse({'ok': False, 'error': 'Cannot log future dates'}, status=400)

    log, created = HabitLog.objects.get_or_create(
        habit=habit, date=log_date,
        defaults={'completed': True},
    )
    if not created:
        # Already existed — delete it (toggle off)
        log.delete()
        done = False
    else:
        done = True

    return JsonResponse({
        'ok':             True,
        'done':           done,
        'current_streak': habit.current_streak,
        'longest_streak': habit.longest_streak,
        'total':          habit.total_completions,
        'rate':           habit.completion_rate,
    })


@login_required
@require_POST
def habit_delete(request, habit_id):
    habit = get_object_or_404(Habit, pk=habit_id, user=request.user)
    name  = habit.name
    habit.delete()
    messages.success(request, f'Habit "{name}" deleted.')
    return redirect('habits')


@login_required
@require_POST
def habit_archive(request, habit_id):
    habit             = get_object_or_404(Habit, pk=habit_id, user=request.user)
    habit.is_archived = True
    habit.save(update_fields=['is_archived'])
    messages.success(request, f'Habit "{habit.name}" archived.')
    return redirect('habits')


@login_required
def habit_edit(request, habit_id):
    habit = get_object_or_404(Habit, pk=habit_id, user=request.user)
    if request.method == 'POST':
        form = HabitForm(request.POST, instance=habit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Habit updated.')
            return redirect('habits')
    else:
        form = HabitForm(instance=habit)
    return render(request, 'habits/habit_form.html', {'form': form, 'habit': habit})