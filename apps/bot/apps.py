from django.apps import AppConfig


class BotConfig(AppConfig):
    name = 'apps.bot'
    verbose_name = "Боты ВК/ТГ и API"

    def ready(self):
        """
        Метод запускается единожды на старте
        """
        super().ready()
        self.delete_activity_keys()

    @staticmethod
    def delete_activity_keys():
        """
        Если сервер был перезапущен в момент, когда бот что-то присылал и ставил activity необходимо очищать такие
        ключи, чтобы бот не слал активити вечно
        """
        from django.core.cache import cache

        activity_keys = cache.keys("activity_*")
        for key in activity_keys:
            cache.delete(key)
