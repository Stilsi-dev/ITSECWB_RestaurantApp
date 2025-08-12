from datetime import timedelta
from functools import wraps
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib import messages
from django.conf import settings

def require_recent_auth(view_func):
    """
    2.1.13: Require re-authentication before critical operations.
    After successful reauth, we store 'reauth_at' in session. Valid for N minutes.
    """
    window = getattr(settings, "REAUTH_TIMEOUT_MINUTES", 5)

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        ra = request.session.get("reauth_at")
        if ra:
            ra = timezone.datetime.fromisoformat(ra)
            if timezone.now() < ra + timedelta(minutes=window):
                return view_func(request, *args, **kwargs)
        messages.warning(request, "Please confirm your password to continue.")
        request.session["post_reauth_next"] = request.get_full_path()
        return redirect("accounts:reauth")
    return _wrapped
