# project/celery.py
from __future__ import annotations
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_autosend.settings")

app = Celery("django_autosend")

# Use Django settings with "CELERY_" prefix or custom config below
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in installed apps
app.autodiscover_tasks()
