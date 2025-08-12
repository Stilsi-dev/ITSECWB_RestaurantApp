# restaurant_project/error_views.py
from django.shortcuts import render
from django.views.decorators.csrf import requires_csrf_token
from django.http import HttpRequest, HttpResponse
import logging

from logs.utils import audit_log  # <— add this

log = logging.getLogger("django")

def _user(request):
    u = getattr(request, "user", None)
    return u if getattr(u, "is_authenticated", False) else None

def _render(request: HttpRequest, template: str, status: int) -> HttpResponse:
    # Never leak internals; render a tame page
    return render(request, template, {"path": request.path}, status=status)

def error_400(request, exception):
    log.info("400 at %s: %s", request.path, exception)
    audit_log(request, _user(request), "HTTP 400 Bad Request", "fail")
    return _render(request, "errors/400.html", 400)

def error_403(request, exception):
    log.warning("403 at %s: %s", request.path, exception)
    audit_log(request, _user(request), "HTTP 403 Forbidden", "fail")
    return _render(request, "errors/403.html", 403)

def error_404(request, exception):
    log.info("404 at %s", request.path)
    audit_log(request, _user(request), "HTTP 404 Not Found", "fail")
    return _render(request, "errors/404.html", 404)

@requires_csrf_token
def error_403_csrf(request, reason=""):
    log.warning("CSRF failure at %s: %s", request.path, reason)
    audit_log(request, _user(request), "CSRF failure", "fail")
    return _render(request, "errors/csrf.html", 403)

def error_500(request):
    log.exception("500 at %s", request.path)  # traceback goes to server logs
    audit_log(request, _user(request), "HTTP 500 Server Error", "fail")
    return _render(request, "errors/500.html", 500)
