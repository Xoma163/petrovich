from django.apps import AppConfig


class MemeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.commands.meme'
    verbose_name = "Команды мемов"
