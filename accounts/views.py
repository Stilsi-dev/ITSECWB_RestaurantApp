from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

User = get_user_model()


@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Uses Django's AuthenticationForm for validation, but the template renders
    plain <input> fields so the text boxes always show.
    """
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Respect ?next= if present
            nxt = request.GET.get("next") or request.POST.get("next")
            return redirect(nxt or "accounts:dashboard")
        else:
            messages.error(request, "Invalid username and/or password.")

    return render(request, "accounts/login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def register_view(request):
    """
    Simple registration: username, email, password, confirm password.
    Fields always render because the template uses plain <input>s.
    """
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    # Values to refill the form after a failed POST
    data = {
        "username": (request.POST.get("username") or "").strip(),
        "email": (request.POST.get("email") or "").strip(),
    }
    errors = {"username": [], "email": [], "password1": [], "password2": [], "non_field": []}

    if request.method == "POST":
        username = data["username"]
        email = data["email"]
        password1 = request.POST.get("password1") or ""
        password2 = request.POST.get("password2") or ""

        # --- validations ---
        if not username:
            errors["username"].append("Username is required.")
        elif User.objects.filter(username=username).exists():
            errors["username"].append("This username is already taken.")

        if not email:
            errors["email"].append("Email is required.")
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors["email"].append("Enter a valid email address.")
            else:
                # Only check uniqueness if User model has 'email' field
                if hasattr(User, "email") and User.objects.filter(email=email).exists():
                    errors["email"].append("This email is already in use.")

        if not password1:
            errors["password1"].append("Password is required.")
        elif len(password1) < 8:
            errors["password1"].append("Password must be at least 8 characters.")

        if not password2:
            errors["password2"].append("Please confirm your password.")
        elif password1 and password1 != password2:
            errors["password2"].append("Passwords do not match.")

        # If no errors, create the user
        has_errors = any(errors[k] for k in errors if k != "non_field")
        if not has_errors:
            user = User.objects.create_user(
                username=username,
                email=email if hasattr(User, "email") else None,
                password=password1,
            )
            # If your custom user has a 'role', choose a default (optional)
            if hasattr(user, "role") and not getattr(user, "role", None):
                user.role = "customer"
                user.save()

            messages.success(request, "Account created! Please log in.")
            return redirect("accounts:login")

        messages.error(request, "Please fix the errors below.")

    return render(request, "accounts/register.html", {"data": data, "errors": errors})


@login_required
def dashboard_view(request):
    """
    Route users to a role-based dashboard template if you have them.
    Fallback to a generic dashboard if role isn’t present.
    """
    role = getattr(request.user, "role", None)

    if role == "admin":
        tpl = "dashboard_admin.html"
    elif role == "manager":
        tpl = "dashboard_manager.html"
    else:
        # customer / unknown
        tpl = "dashboard_customer.html" if role == "customer" else "dashboard.html"

    return render(request, tpl)


@login_required
def manage_users_view(request):
    """
    Only admins can access.
    """
    if getattr(request.user, "role", None) != "admin":
        messages.error(request, "Not authorized!")
        return redirect("accounts:dashboard")

    users = User.objects.all().order_by("username")
    return render(request, "accounts/manage_users.html", {"users": users})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")
