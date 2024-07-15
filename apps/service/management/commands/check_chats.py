from django.core.management.base import BaseCommand

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.models import Chat


class Command(BaseCommand):

    def handle(self, *args, **options):
        tg_bot = TgBot()

        for chat in Chat.objects.all():
            if not tg_bot.get_chat(chat.chat_id)['ok']:
                chat.kicked = True
                chat.save()
