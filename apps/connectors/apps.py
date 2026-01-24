from django.apps import AppConfig


class ConnectorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.connectors'
    verbose_name = "Коннекторы (API и парсеры)"
