from django.core.management.base import BaseCommand

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.models import UserSettings, ChatSettings

tg_bot = TgBot()


class Command(BaseCommand):
    def handle(self, *args, **options):
        uss = UserSettings.objects.filter(profile__isnull=True)
        uss.delete()

        css = ChatSettings.objects.filter(chat__isnull=True)
        css.delete()
