"""WSGI entry point. Defaults to production settings; development uses `manage.py runserver`."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.prod")

application = get_wsgi_application()
