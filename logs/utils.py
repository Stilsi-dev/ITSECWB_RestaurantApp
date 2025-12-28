"""Centralized audit logging helper.

The application uses an explicit audit trail (separate from Django's server logs)
to record security- and business-relevant events. This helper is intentionally
best-effort and must never raise: failures to write logs should not block user
flows.
"""

from logs.models import Log

def audit_log(request, user, action: str, status: str = "info", extra: str | None = None):
    """
        Write an audit record.

        - Best-effort, never raises.
        - `status` is one of: `success`, `fail`, `info`.
        - `extra` (if provided) is appended to the action message and truncated to
            fit within the database column.
        - Captures client IP address and User-Agent (best-effort) from the request.
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
