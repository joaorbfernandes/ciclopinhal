"""Production. Every value comes from the environment and a missing one stops the process at start-up."""

from django.core.exceptions import ImproperlyConfigured

from backend.config import env
from backend.config.settings.base import *

DEBUG = env.get_bool("DEBUG", default=False)
if DEBUG:
    raise ImproperlyConfigured("DEBUG must be False in production settings")

SECRET_KEY = env.get_str("SECRET_KEY")
ALLOWED_HOSTS = env.get_list("ALLOWED_HOSTS")

DATABASES = {"default": database_settings(local=False)}

# HTTPS, secure cookies and HSTS are introduced in Phases 2-3 (docs/engineering.md §7). Until then Django's
# `check --deploy` warnings for them stay visible; `make deploy-check` tracks them in deploy-warnings-deferred.txt.
