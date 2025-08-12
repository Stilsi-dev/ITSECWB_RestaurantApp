# accounts/views.py
from __future__ import annotations

from datetime import timedelta
from functools import wraps
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .models import PasswordHistory

# Prefer the centralized audit util; keep a safe fallback if it's missing
try:
    from logs.utils import audit_log  # type: ignore
except Exception:  # pragma: no cover
    def audit_log(request, user, action, outcome):
        # Soft fallback: don't break app if logs app not present
        pass

log = logging.getLogger("django")
User = get_user_model()

# Reasonable, non-leading security questions
SECURITY_QUESTION_CHOICES = [
    "What was the name of your first stuffed animal?",
    "What was your childhood nickname at home?",
    "What was the model of your first mobile phone?",
    "What is a memorable place only you would know (do not use your hometown)?",
    "What was your least favorite subject in school?",
    "What’s the name of a teacher who impacted you (not your favorite)?",
    "What is the title of a book you strongly disliked?",
]

# -----------------------------
# Helpers
# -----------------------------

def _fail_secure_forbidden(request, action: str):
    """Return a generic 403 and log access-control failure."""
    user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
    audit_log(request, user, action, "fail")
    log.warning("Access control failure: user=%s path=%s action=%s", user, request.path, action)
    return HttpResponseForbidden("You are not allowed to perform this action.")


def _hash_answer(raw: str) -> str:
    """Hash the security answer using the same hasher as passwords (simple + strong)."""
    from django.contrib.auth.hashers import make_password
    return make_password(raw.strip())


def _check_answer(raw: str, hashed: str) -> bool:
    from django.contrib.auth.hashers import check_password
    try:
        return check_password(raw.strip(), hashed or "")
    except Exception:
        return False


def _password_recently_changed(user: User, min_days: int) -> bool:
    """Return True if password was changed within the last `min_days` days."""
    when = getattr(user, "password_changed_at", None)
    if not when:
        return False
    return timezone.now() - when < timedelta(days=min_days)


def _is_reused_password(user: User, raw_password: str, history_count: int) -> bool:
    """Check raw_password against last N password hashes stored in PasswordHistory."""
    from django.contrib.auth.hashers import check_password
    recent = (
        PasswordHistory.objects.filter(user=user)
        .order_by("-changed_at")
        .values_list("password_hash", flat=True)[: max(0, history_count)]
    )
    for ph in recent:
        try:
            if check_password(raw_password, ph):
                return True
        except Exception:
            continue
    return False


def _remember_password(user: User):
    """Store current password hash to history and stamp password_changed_at."""
    PasswordHistory.objects.create(user=user, password_hash=user.password)
    user.password_changed_at = timezone.now()
    user.save(update_fields=["password_changed_at"])


def _settings_int(name: str, default: int) -> int:
    val = getattr(settings, name, default)
    try:
        return int(val)
    except Exception:
        return default


# -----------------------------
# Re-authentication (2.1.13)
# -----------------------------

def require_recent_reauth(viewfunc):
    """
    Decorator for critical operations.
    If the user hasn’t re-authed within REAUTH_TIMEOUT_MINUTES, send them to /reauth/?next=...
    """
    @wraps(viewfunc)
    @login_required
    def _wrapped(request, *args, **kwargs):
        ts = request.session.get("reauth_at")
        timeout = _settings_int("REAUTH_TIMEOUT_MINUTES", 5)

        valid_at = None
        if ts:
            try:
                valid_at = timezone.datetime.fromisoformat(ts)
                if timezone.is_naive(valid_at):
                    valid_at = timezone.make_aware(valid_at, timezone.get_current_timezone())
            except Exception:
                valid_at = None

        if not valid_at or (timezone.now() - valid_at) > timedelta(minutes=timeout):
            return redirect(f"/reauth/?next={request.get_full_path()}")

        return viewfunc(request, *args, **kwargs)

    return _wrapped


# -----------------------------
# Login / Register / Logout
# -----------------------------

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        user_for_msg = None
        if username:
            try:
                user_for_msg = User.objects.filter(username=username).first()
            except Exception:
                user_for_msg = None

        if form.is_valid():
            user = form.get_user()

            # Enforce lockout defensively here in case the backend doesn’t block it:
            locked_until = getattr(user, "locked_until", None)
            if locked_until and timezone.now() < locked_until:
                messages.error(
                    request,
                    f"Account temporarily locked due to failed attempts. "
                    f"Try again after {locked_until.strftime('%Y-%m-%d %H:%M')}."
                )
                audit_log(request, user, "Login attempt during lockout", "fail")
                return redirect("accounts:login")

            # Compute the "last use" banner BEFORE we call login()
            # - previous successful login -> user.last_login (if available)
            # - last failed attempt -> from cache set by signals
            prev_success = user.last_login  # may be None on first login
            last_failed = cache.get(f"last_failed_auth:{user.username}") or {}

            # Now log the user in
            login(request, user)
            audit_log(request, user, "User logged in", "success")

            # Build and show the banner exactly once
            banner = None
            # Choose most recent between prev_success and last_failed["ts"]
            ts_success = prev_success
            ts_failed = None
            try:
                if last_failed.get("ts"):
                    ts_failed = timezone.datetime.fromisoformat(last_failed["ts"])
                    if timezone.is_naive(ts_failed):
                        ts_failed = timezone.make_aware(ts_failed, timezone.get_current_timezone())
            except Exception:
                ts_failed = None

            # Decide which to show
            show_failed = ts_failed and (not ts_success or ts_failed > ts_success)
            if show_failed:
                when = ts_failed.astimezone(timezone.get_current_timezone()).strftime("%Y-%m-%d %H:%M")
                ip = last_failed.get("ip")
                banner = f"Last account use: failed login on {when}" + (f" from {ip}" if ip else "")
            elif ts_success:
                when = ts_success.astimezone(timezone.get_current_timezone()).strftime("%Y-%m-%d %H:%M")
                banner = f"Last account use: successful login on {when}"

            if banner:
                messages.info(request, banner)

            nxt = request.GET.get("next") or request.POST.get("next")
            return redirect(nxt or "accounts:dashboard")

        # invalid login — generic error (don’t leak which part failed)
        locked_until = getattr(user_for_msg, "locked_until", None)
        if locked_until and timezone.now() < locked_until:
            messages.error(
                request,
                f"Account temporarily locked due to failed attempts. Try again after {locked_until.strftime('%Y-%m-%d %H:%M')}."
            )
        else:
            messages.error(request, "Invalid username and/or password.")
        audit_log(request, user_for_msg or None, "Login attempt", "fail")
        log.warning("Authentication failure for username=%s path=%s", username, request.path)

    return render(request, "accounts/login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

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

        # username
        if not username:
            errors["username"].append("Username is required.")
        elif User.objects.filter(username=username).exists():
            errors["username"].append("This username is already taken.")

        # email
        if not email:
            errors["email"].append("Email is required.")
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors["email"].append("Enter a valid email address.")
            else:
                if hasattr(User, "email") and User.objects.filter(email=email).exists():
                    errors["email"].append("This email is already in use.")

        # passwords
        if not password1:
            errors["password1"].append("Password is required.")
        elif len(password1) < 8:
            errors["password1"].append("Password must be at least 8 characters.")

        if not password2:
            errors["password2"].append("Please confirm your password.")
        elif password1 and password1 != password2:
            errors["password2"].append("Passwords do not match.")

        # finalize
        has_errors = any(errors[k] for k in errors if k != "non_field")
        if not has_errors:
            user = User.objects.create_user(
                username=username,
                email=email if hasattr(User, "email") else None,
                password=password1,
            )
            # default role
            if hasattr(user, "role") and not getattr(user, "role", None):
                user.role = "customer"
                user.save(update_fields=["role"])

            # seed password history stamp
            _remember_password(user)

            audit_log(request, user, "User registered", "success")
            messages.success(request, "Account created! Please set your security question.")
            # Force login for convenience, then go to setup-security-question
            login(request, user)
            return redirect("accounts:setup_security_question")

        # validation failure
        audit_log(request, None, "Registration validation failed", "fail")
        log.warning("Registration validation errors: %s", errors)
        messages.error(request, "Please fix the errors below.")

    return render(request, "accounts/register.html", {"data": data, "errors": errors})


@login_required
def logout_view(request):
    audit_log(request, request.user, "User logged out", "success")
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")


# -----------------------------
# Dashboard / Manage users (simple)
# -----------------------------

@login_required
def dashboard_view(request):
    role = getattr(request.user, "role", None)
    if role == "admin":
        tpl = "dashboard_admin.html"
    elif role == "manager":
        tpl = "dashboard_manager.html"
    else:
        tpl = "dashboard_customer.html" if role == "customer" else "dashboard.html"

    audit_log(request, request.user, "Viewed dashboard", "success")
    return render(request, tpl)


@login_required
@require_http_methods(["GET", "POST"])
@require_recent_reauth  # critical: role changes require fresh auth
def manage_users_view(request):
    if getattr(request.user, "role", None) != "admin":
        return _fail_secure_forbidden(request, "Manage users (admin-only)")

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        new_role = request.POST.get("role")

        if new_role not in ("customer", "manager", "admin"):
            messages.error(request, "Invalid role.")
            return redirect("accounts:manage_users")

        target = get_object_or_404(User, pk=user_id)

        # Prevent removing the last admin
        if target.role == "admin" and new_role != "admin":
            other_admin_exists = User.objects.exclude(pk=target.pk).filter(role="admin").exists()
            if not other_admin_exists:
                messages.error(request, "You can't remove the last admin.")
                return redirect("accounts:manage_users")

        # Persist role and align Django flags
        target.role = new_role
        target.is_staff = new_role in ("manager", "admin")
        target.is_superuser = new_role == "admin"
        target.save(update_fields=["role", "is_staff", "is_superuser"])

        audit_log(request, request.user, f"Changed role for {target.username} to {new_role}", "success")
        messages.success(request, f"Updated {target.username} to {new_role.title()}.")
        return redirect("accounts:manage_users")

    users = User.objects.all().order_by("username")
    audit_log(request, request.user, "Viewed manage users", "success")
    return render(request, "accounts/manage_users.html", {"users": users})


# -----------------------------
# Re-authentication views
# -----------------------------

@login_required
@require_http_methods(["GET", "POST"])
def reauth_view(request):
    """
    Ask the logged-in user to enter their password again.
    On success, store a timestamp in session and redirect to ?next=... (or dashboard).
    """
    if request.method == "POST":
        pwd = request.POST.get("password", "")
        if request.user.check_password(pwd):
            request.session["reauth_at"] = timezone.now().isoformat()
            audit_log(request, request.user, "Re-authentication", "success")
            messages.success(request, "Re-authenticated.")
            nxt = request.POST.get("next") or request.GET.get("next")
            return redirect(nxt or "accounts:dashboard")

        audit_log(request, request.user, "Re-authentication", "fail")
        log.warning("Re-authentication failure user=%s path=%s", request.user, request.path)
        messages.error(request, "Incorrect password. Please try again.")

    context = {"next": request.GET.get("next", "")}
    return render(request, "accounts/reauth.html", context)


# -----------------------------
# Security Question setup (2.1.9)
# -----------------------------

@login_required
@require_http_methods(["GET", "POST"])
def setup_security_question_view(request):
    """
    Force users to set a security question/answer if they don't have one yet.
    """
    user = request.user
    question_existing = (getattr(user, "security_question", "") or "").strip()
    answer_existing = (getattr(user, "security_answer_hash", "") or "").strip()

    if question_existing and answer_existing:
        messages.info(request, "Your security question is already set.")
        return redirect("accounts:dashboard")

    if request.method == "POST":
        q = (request.POST.get("question") or "").strip()
        a = (request.POST.get("answer") or "").strip()

        errs = []
        if not q:
            errs.append("Please select a question.")
        elif q not in SECURITY_QUESTION_CHOICES:
            errs.append("Invalid question selected.")

        if not a:
            errs.append("Please provide an answer.")
        elif len(a) < 6:
            errs.append("Answer must be at least 6 characters.")
        else:
            # basic entropy/triviality checks
            simple = {"password", "qwerty", "123456", "abcdef", "iloveyou", "unknown", "n/a"}
            if a.lower() in simple:
                errs.append("Answer is too common; choose something more unique.")
            if len(set(a.lower())) <= 2:
                errs.append("Answer appears too simple; add more variety.")
            uname = (getattr(user, "username", "") or "").lower()
            mail_local = ((getattr(user, "email", "") or "").lower().split("@")[0]) if getattr(user, "email", None) else ""
            if uname and uname in a.lower():
                errs.append("Answer should not contain your username.")
            if mail_local and mail_local in a.lower():
                errs.append("Answer should not contain your email local-part.")

        if errs:
            audit_log(request, user, "Setup security question validation failed", "fail")
            log.warning("Security question setup validation errors: %s", errs)
            for e in errs:
                messages.error(request, e)
        else:
            user.security_question = q
            user.security_answer_hash = _hash_answer(a)
            user.save(update_fields=["security_question", "security_answer_hash"])
            audit_log(request, user, "Security question set", "success")
            messages.success(request, "Security question saved.")
            return redirect("accounts:dashboard")

    return render(
        request,
        "accounts/setup_security_question.html",
        {"questions": SECURITY_QUESTION_CHOICES},
    )


# -----------------------------
# Change password (2.1.10 + 2.1.11)
# -----------------------------

@login_required
@require_http_methods(["GET", "POST"])
@require_recent_reauth  # critical operation
def change_password_view(request):
    """
    User-initiated password change:
    - Must provide current password
    - Enforce min password age
    - Prevent password re-use (history)
    """
    user = request.user
    min_days = _settings_int("MIN_PASSWORD_AGE_DAYS", 1)
    hist_n = _settings_int("PASSWORD_HISTORY_COUNT", 5)

    if request.method == "POST":
        current = request.POST.get("current_password") or ""
        new1 = request.POST.get("new_password1") or ""
        new2 = request.POST.get("new_password2") or ""

        errs = []

        if not user.check_password(current):
            errs.append("Current password is incorrect.")

        if _password_recently_changed(user, min_days):
            errs.append(f"Password was changed recently. Please wait at least {min_days} day(s) before changing again.")

        if not new1 or not new2:
            errs.append("Please enter and confirm your new password.")
        elif new1 != new2:
            errs.append("New passwords do not match.")
        elif len(new1) < 12:
            errs.append("New password must be at least 12 characters.")
        elif _is_reused_password(user, new1, hist_n):
            errs.append("You cannot reuse a recent password.")

        if errs:
            audit_log(request, user, "Change password validation failed", "fail")
            log.warning("Change password validation errors for user=%s: %s", user, errs)
            for e in errs:
                messages.error(request, e)
        else:
            # Save old hash to history, then set new
            _remember_password(user)  # store current before change
            user.set_password(new1)
            user.save()
            _remember_password(user)  # now remember the new one (stamps password_changed_at)

            # Re-authenticate session
            login(request, user)
            audit_log(request, user, "Password changed", "success")
            messages.success(request, "Password changed successfully.")
            return redirect("accounts:dashboard")

    return render(request, "accounts/change_password.html")


# -----------------------------
# Password Reset via Security Question (2.1.9 + 2.1.10 + 2.1.11)
# -----------------------------

@require_http_methods(["GET", "POST"])
def reset_start_view(request):
    """
    Step 1: Ask for username.
    Store target user id in session if found, but do not reveal existence.
    """
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        user = None
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = None

        # Never reveal if user exists. If exists and has SQ, store id.
        if user and (getattr(user, "security_question", "") or "").strip():
            request.session["pwreset_uid"] = user.id
        else:
            request.session.pop("pwreset_uid", None)

        audit_log(request, user if user else None, "Password reset start", "success")
        return redirect("accounts:reset_question")

    return render(request, "accounts/reset_start.html")


@require_http_methods(["GET", "POST"])
def reset_question_view(request):
    """
    Step 2: Show the stored user's security question and check the answer.
    """
    uid = request.session.get("pwreset_uid")
    user = None
    if uid:
        try:
            user = User.objects.get(pk=uid)
        except User.DoesNotExist:
            user = None

    # If no valid stored user, bounce back to start (fail securely)
    if not user:
        audit_log(request, None, "Password reset question without session", "fail")
        return redirect("accounts:reset_start")

    question = (getattr(user, "security_question", "") or "").strip()
    if not question:
        # No SQ set; don't leak that—just restart flow
        audit_log(request, user, "Password reset question missing", "fail")
        return redirect("accounts:reset_start")

    if request.method == "POST":
        ans = (request.POST.get("answer") or "").strip()
        if not ans or not _check_answer(ans, getattr(user, "security_answer_hash", "") or ""):
            audit_log(request, user, "Password reset answer failed", "fail")
            messages.error(request, "Incorrect answer. Please try again.")
        else:
            request.session["pwreset_ans_ok"] = True
            audit_log(request, user, "Password reset answer success", "success")
            return redirect("accounts:reset_set_password")

    return render(request, "accounts/reset_question.html", {"question": question})


@require_http_methods(["GET", "POST"])
def reset_set_password_view(request):
    """
    Step 3: Set a new password after answering the question.
    Enforce min age & history as well.
    """
    uid = request.session.get("pwreset_uid")
    ans_ok = request.session.get("pwreset_ans_ok") is True

    # Must have passed previous steps
    if not uid or not ans_ok:
        audit_log(request, None, "Password reset set without prerequisites", "fail")
        return redirect("accounts:reset_start")

    user = get_object_or_404(User, pk=uid)
    min_days = _settings_int("MIN_PASSWORD_AGE_DAYS", 1)
    hist_n = _settings_int("PASSWORD_HISTORY_COUNT", 5)

    if request.method == "POST":
        new1 = request.POST.get("new_password1") or ""
        new2 = request.POST.get("new_password2") or ""

        errs = []
        if _password_recently_changed(user, min_days):
            errs.append(f"You changed your password recently. Please wait at least {min_days} day(s).")

        if not new1 or not new2:
            errs.append("Please enter and confirm your new password.")
        elif new1 != new2:
            errs.append("New passwords do not match.")
        elif len(new1) < 12:
            errs.append("New password must be at least 12 characters.")
        elif _is_reused_password(user, new1, hist_n):
            errs.append("You cannot reuse a recent password.")

        if errs:
            audit_log(request, user, "Password reset set validation failed", "fail")
            log.warning("Password reset set validation errors user=%s: %s", user, errs)
            for e in errs:
                messages.error(request, e)
        else:
            # Save old hash to history, then set new
            _remember_password(user)  # store current before change
            user.set_password(new1)
            user.save()
            _remember_password(user)  # now remember the new one

            # Cleanup reset session markers
            request.session.pop("pwreset_uid", None)
            request.session.pop("pwreset_ans_ok", None)

            audit_log(request, user, "Password reset completed", "success")
            messages.success(request, "Password reset successful. Please log in.")
            return redirect("accounts:login")

    return render(request, "accounts/reset_set_password.html")
