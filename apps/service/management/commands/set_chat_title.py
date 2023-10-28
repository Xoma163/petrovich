from time import sleep

from django.core.management.base import BaseCommand

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.models import Chat

tg_bot = TgBot()


class Command(BaseCommand):

    def handle(self, *args, **options):
        chats = Chat.objects.all()
        for chat in chats:
            data = tg_bot.requests.get('getChat', params={"chat_id": chat.chat_id})
            data = data.json()
            if data['ok']:
                if 'title' in data['result']:
                    title = data['result']['title']
                    chat.name = title
                    chat.kicked = False
                    chat.save()
                else:
                    print(f"something wrong. pk={chat.pk}")
            else:
                chat.kicked = True
                chat.save()

            sleep(1)
