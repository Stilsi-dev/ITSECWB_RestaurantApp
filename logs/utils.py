# logs/utils.py
from logs.models import Log

def audit_log(request, user, action: str, status: str = "info", extra: str | None = None):
    """
    Best-effort, never raises. `status` is 'success' | 'fail' | 'info'.
    `extra` (if provided) is appended to action (truncated to fit column).
    """
    try:
        ua = (request.META.get("HTTP_USER_AGENT") or "")[:1024]
        ip = request.META.get("REMOTE_ADDR") or None
        user_obj = user if getattr(user, "pk", None) else None

        msg = action
        if extra:
            # fit into CharField(255)
            leftover = 255 - len(action) - 3
            msg = f"{action} ({extra[:max(0,leftover)]})"

        Log.objects.create(
            user=user_obj,
            action=msg[:255],
            status=status,
            ip_address=ip,
            user_agent=ua,
        )
    except Exception:
        # Never let logging break business flow.
        pass
