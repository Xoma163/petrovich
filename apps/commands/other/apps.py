from django.apps import AppConfig


class OtherConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.commands.other'
    verbose_name = "Команды остальные"
