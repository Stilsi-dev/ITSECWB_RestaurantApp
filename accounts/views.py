from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from .models import User
from logs.models import Log


# Register
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'customer'  # Set default role
            user.save()

            # Log successful registration
            Log.objects.create(
                user=user,
                action="New user registered",
                ip_address=request.META.get('REMOTE_ADDR'),
                status='success'
            )
            messages.success(request, "✅ Account created successfully! Please login.")
            return redirect('login')

        else:
            # Log failed registration
            Log.objects.create(
                user=None,
                action="Failed registration attempt",
                ip_address=request.META.get('REMOTE_ADDR'),
                status='fail'
            )
            messages.error(request, "⚠️ Please correct the errors highlighted below.")
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


# Login
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            if getattr(user, "is_locked", False):
                messages.error(request, "🚫 Your account is locked. Please contact admin.")
                Log.objects.create(
                    user=user,
                    action="Login attempt on locked account",
                    ip_address=request.META.get('REMOTE_ADDR'),
                    status='fail'
                )
                return redirect('login')

            login(request, user)

            Log.objects.create(
                user=user,
                action="User logged in",
                ip_address=request.META.get('REMOTE_ADDR'),
                status='success'
            )
            return redirect('dashboard')
        else:
            # Invalid login
            Log.objects.create(
                user=None,
                action=f"Failed login attempt for username: {request.POST.get('username')}",
                ip_address=request.META.get('REMOTE_ADDR'),
                status='fail'
            )
            messages.error(request, "❌ Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


# Dashboard
@login_required
def dashboard_view(request):
    Log.objects.create(
        user=request.user,
        action="Viewed dashboard",
        ip_address=request.META.get('REMOTE_ADDR'),
        status='success'
    )

    if request.user.role == 'admin':
        return render(request, 'dashboard_admin.html')
    elif request.user.role == 'manager':
        return render(request, 'dashboard_manager.html')
    else:
        return render(request, 'dashboard_customer.html')


# Logout
@login_required
def logout_view(request):
    Log.objects.create(
        user=request.user,
        action="User logged out",
        ip_address=request.META.get('REMOTE_ADDR'),
        status='success'
    )
    logout(request)
    return redirect('login')


# Manage Users (Admin only)
@login_required
@user_passes_test(lambda u: u.role == 'admin')
def manage_users_view(request):
    users = User.objects.exclude(id=request.user.id)  # Exclude admin itself

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_role = request.POST.get('role')
        user = get_object_or_404(User, id=user_id)

        old_role = user.role
        user.role = new_role
        user.save()

        Log.objects.create(
            user=request.user,
            action=f"Changed {user.username}'s role from {old_role} to {new_role}",
            ip_address=request.META.get('REMOTE_ADDR'),
            status='success'
        )
        messages.success(request, f"{user.username}'s role updated to {new_role}.")

    return render(request, 'accounts/manage_users.html', {'users': users})
