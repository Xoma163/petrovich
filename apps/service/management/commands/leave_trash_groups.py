from django.core.management.base import BaseCommand

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.models import Chat


class Command(BaseCommand):

    def handle(self, *args, **options):
        pks = [146, 116, 133, 123, 115, 72, 125, 134, 144]

        chats = Chat.objects.filter(pk__in=pks)
        tg_bot = TgBot()
        for chat in chats:
            tg_bot.leave_group(chat.chat_id)
            chat.kicked = True
            chat.save()
