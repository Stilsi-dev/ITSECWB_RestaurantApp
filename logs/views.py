# logs/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Value
from django.db.models.functions import Lower

from .models import Log

User = get_user_model()

@login_required
def admin_logs_view(request):
    # Only admins allowed
    if getattr(request.user, "role", "") != "admin" and not request.user.is_superuser:
        messages.error(request, "Not authorized!")
        return redirect("accounts:dashboard")

    qs = Log.objects.select_related("user").all()

    # --- Filters ---
    user_filter = request.GET.get("user") or ""
    action_filter = request.GET.get("action") or ""
    status_filter = request.GET.get("status") or ""

    if user_filter:
        if user_filter.isdigit():
            qs = qs.filter(user_id=user_filter)
        else:
            qs = qs.filter(user__username=user_filter)

    if action_filter:
        qs = qs.filter(action__icontains=action_filter)

    if status_filter:
        qs = qs.filter(status=status_filter)

    # --- Sorting (whitelist) ---
    sort = request.GET.get("sort") or "-timestamp"
    allowed_sorts = {"timestamp", "-timestamp", "user__username", "-user__username", "status", "-status"}
    if sort not in allowed_sorts:
        sort = "-timestamp"
    qs = qs.order_by(sort)

    # Distinct actions for the filter dropdown (case-insensitive, sorted)
    actions = (
        Log.objects.exclude(action__isnull=True)
        .exclude(action__exact="")
        .annotate(a=Lower("action"))
        .order_by("a")
        .values_list("action", flat=True)
        .distinct()
    )

    users = User.objects.order_by("username")

    # Optional pagination
    paginator = Paginator(qs, 25)  # 25 per page
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "logs/admin_logs.html",
        {
            "logs": page_obj.object_list,
            "page_obj": page_obj,
            "users": users,
            "actions": actions,
            "selected_user": user_filter,
            "selected_action": action_filter,
            "selected_status": status_filter,
            "sort": sort,
        },
    )
