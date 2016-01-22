from django.apps import AppConfig


class SlothAuthConfig(AppConfig):
    name = 'slothauth'

    def ready(self):
        from . import signals
