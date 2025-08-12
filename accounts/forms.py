from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm
from .models import User


class RegisterForm(UserCreationForm):
    # Optional: if you want to switch register_view to use this form
    security_question = forms.CharField(
        required=True,
        help_text="Use a specific question only you can answer (≥ 20 characters).",
    )
    security_answer = forms.CharField(
        required=True,
        widget=forms.PasswordInput,
        help_text="Treat it like a password (≥ 8 characters).",
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "security_question", "security_answer"]


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Password"}))


# Password reset flow (username -> question -> set new pw)
class ResetUsernameForm(forms.Form):
    username = forms.CharField(max_length=150, label="Username")


class SecurityAnswerForm(forms.Form):
    answer = forms.CharField(
        label="Answer to your security question",
        widget=forms.PasswordInput,
    )


class ResetSetPasswordForm(SetPasswordForm):
    """
    Inherits Django's SetPasswordForm so ALL validators apply:
    - Minimum length + complexity
    - PasswordHistoryValidator (no reuse)
    - MinimumPasswordAgeValidator (≥ 1 day unless configured otherwise)
    """
    pass
