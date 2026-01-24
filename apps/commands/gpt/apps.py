from django.apps import AppConfig


class GptConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.commands.gpt'
    verbose_name = 'Команды GPT'
