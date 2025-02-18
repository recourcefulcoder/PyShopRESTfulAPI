import os
import subprocess

from django.apps import AppConfig
from django.conf import settings


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self):
        if settings.DEBUG and os.environ.get("RUN_MAIN"):
            subprocess.Popen("redis-server --port 6379", shell=True)
