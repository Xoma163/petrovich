from django.core.management.base import BaseCommand

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.models import Chat

tg_bot = TgBot()


class Command(BaseCommand):
    def handle(self, *args, **options):
        chat_pks = [150, 153, 154, 155]
        chats = Chat.objects.filter(pk__in=chat_pks)
        for chat in chats:
            tg_bot.leave_group(chat.chat_id)
            chat.kicked = True
            chat.save()
