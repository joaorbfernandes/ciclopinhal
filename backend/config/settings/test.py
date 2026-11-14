"""Test runs (pytest-django). PostgreSQL only; never SQLite."""

from backend.config.settings.base import *

DEBUG = False
SECRET_KEY = "test-only-not-a-secret"
ALLOWED_HOSTS = ["testserver", "localhost"]

DATABASES = {"default": database_settings(local=True)}
