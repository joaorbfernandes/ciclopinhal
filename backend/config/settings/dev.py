"""Local development on the host or in the Compose `app` service."""

from backend.config.settings.base import *

DEBUG = True
SECRET_KEY = "dev-only-not-a-secret"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

DATABASES = {"default": database_settings(local=True)}
