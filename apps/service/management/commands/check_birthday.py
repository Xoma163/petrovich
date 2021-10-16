from datetime import datetime

from django.core.management.base import BaseCommand

from apps.bot.classes.bots.TgBot import TgBot
from apps.bot.models import Chat, Users
from apps.games.models import Gamer

tg_bot = TgBot()


class Command(BaseCommand):

    def handle(self, *args, **options):
        chat_pks = options['chat_id'][0].split(',')
        for chat_pk in chat_pks:
            chat = Chat.objects.get(pk=chat_pk)
            today = datetime.now()
            users = Users.objects.filter(chats=chat,
                                         birthday__day=today.day,
                                         birthday__month=today.month)

            for user in users:
                if user.celebrate_bday:
                    tg_bot.send_message(chat.chat_id, f"С Днём рождения, {tg_bot.get_mention(user)}!")

                gamer = Gamer.objects.filter(user=user).first()
                if gamer:
                    gamer.roulette_points += 100000
                    gamer.save()
                    tg_bot.send_message(chat.chat_id, "На ваш счет зачислено 100 000 бонусных очков.")

    def add_arguments(self, parser):
        parser.add_argument('chat_id', nargs='+', type=str, help='chat_id')
