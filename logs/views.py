# logs/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Log

User = get_user_model()


@login_required
def admin_logs_view(request):
    if request.user.role != 'admin':
        messages.error(request, "Not authorized!")
        return redirect('dashboard')

    logs = Log.objects.all().order_by('-timestamp')

    # Filters
    user_filter = request.GET.get('user')
    action_filter = request.GET.get('action')
    status_filter = request.GET.get('status')

    if user_filter:
        # Handle if user_filter is username or id
        if user_filter.isdigit():
            logs = logs.filter(user_id=user_filter)
        else:
            logs = logs.filter(user__username=user_filter)

    if action_filter:
        logs = logs.filter(action__icontains=action_filter)

    if status_filter:
        logs = logs.filter(status=status_filter)

    sort_by = request.GET.get('sort', '-timestamp')
    logs = logs.order_by(sort_by)

    users = User.objects.all()

    return render(request, 'logs/admin_logs.html', {
        'logs': logs,
        'users': users,
        'selected_user': user_filter,
        'selected_action': action_filter,
        'selected_status': status_filter,
    })
