from django.apps import AppConfig


class ServiceConfig(AppConfig):
    name = 'apps.service'
    verbose_name = "Сервисы"

    def ready(self):
        import apps.service.signals  # noqa
