"""Settings shared by every environment. Environment modules (dev, test, prod) supply what differs."""

from pathlib import Path
from typing import Any

from backend.config import env

BASE_DIR = Path(__file__).resolve().parents[3]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.config.urls"
WSGI_APPLICATION = "backend.config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "frontend" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "frontend" / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "pt-pt"
TIME_ZONE = "Europe/Lisbon"
USE_I18N = True
# Datetimes are timezone-aware and stored in UTC; TIME_ZONE only sets the default for display and form input.
# Do not set TIME_ZONE inside DATABASES: that changes the stored zone.
USE_TZ = True


def database_settings(*, local: bool) -> dict[str, Any]:
    """PostgreSQL connection from POSTGRES_* variables.

    `local=True` (dev, test) falls back to the credentials of the Docker Compose database, which listens on
    127.0.0.1 only. `local=False` (prod) requires every value to be set.
    """

    def var(name: str, local_default: str) -> str:
        return env.get_str(name, local_default if local else None)

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": var("POSTGRES_DB", "ciclopinhal"),
        "USER": var("POSTGRES_USER", "ciclopinhal"),
        "PASSWORD": var("POSTGRES_PASSWORD", "ciclopinhal"),
        "HOST": var("POSTGRES_HOST", "127.0.0.1"),
        "PORT": var("POSTGRES_PORT", "5433"),
        # ATOMIC_REQUESTS stays at its default (False): use cases own transactions (ADR-0004).
    }
