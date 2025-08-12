import os
from pathlib import Path

# BASE DIR
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-REPLACE_THIS_WITH_A_REAL_SECRET_KEY'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Security headers (defensive; fail-closed where possible)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

CSRF_FAILURE_VIEW = "restaurant_project.error_views.error_403_csrf"

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',

    # Custom apps
    'accounts',   # if you created AccountsConfig + signals, you can also use: 'accounts.apps.AccountsConfig'
    'menu',
    'orders',
    'logs',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'restaurant_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # root-level templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'restaurant_project.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

SECURITY_QUESTIONS = [
    "What was the name of the street you lived on as a child?",
    "What is the middle name of your oldest sibling?",
    "What is the name of the first company you worked for?",
    "What is the name of the first school you attended?",
    "What is your maternal grandmother’s maiden name?",
    "What was the make and model of your first car?",
    "What was the name of your childhood best friend?",
    "In what city did your parents meet?",
    "What is the title of your favorite book from childhood?",
    "What is the name of the hospital where you were born?",
]

# Password history & age
PASSWORD_HISTORY_COUNT = 5          # 2.1.10
MIN_PASSWORD_AGE_DAYS = 1           # 2.1.11

# Re-authenticate before critical ops
REAUTH_TIMEOUT_MINUTES = 5          # 2.1.13 window


# ===== Password validation (2.1.5–2.1.6) =====
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 12}},   # <-- set policy length here (use 8 if needed now)
    {"NAME": "accounts.validators.StrongPasswordValidator"},     # upper/lower/number/special
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "accounts.validators.PasswordHistoryValidator"},
    {"NAME": "accounts.validators.MinimumPasswordAgeValidator"},
]

# ===== Account lockout (2.1.8) =====
# Use custom backend that honors locked accounts (accounts/auth_backends.py)
AUTHENTICATION_BACKENDS = ["accounts.auth_backends.LockoutBackend"]

# Tunables for signals (accounts/signals.py)
LOCKOUT_MAX_FAILURES = 5            # number of consecutive failures before lock
LOCKOUT_COOLDOWN_MINUTES = 15       # lockout duration

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

# Media (optional, for images/files)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication redirects
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# Session Security (optional)
SESSION_COOKIE_AGE = 1800  # 30 minutes
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Logging (includes a 'security' logger for auth events)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'project.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'security': {                      # used by accounts/signals.py
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
