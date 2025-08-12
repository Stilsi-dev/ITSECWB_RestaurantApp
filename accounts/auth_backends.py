from django.contrib.auth.backends import ModelBackend

class LockoutBackend(ModelBackend):
    """Prevents authentication while the account is locked."""
    def user_can_authenticate(self, user):
        ok = super().user_can_authenticate(user)
        if not ok:
            return False
        # If the user model has is_locked_now(), honor it
        checker = getattr(user, "is_locked_now", None)
        return False if callable(checker) and checker() else True
