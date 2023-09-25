from datetime import datetime

from django.core.management.base import BaseCommand

from apps.bot.classes.bots.tg import TgBot
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.models import Chat, Profile
from apps.games.models import Gamer

tg_bot = TgBot()


class Command(BaseCommand):

    def handle(self, *args, **options):
        chat_pks = options['chat_id'][0].split(',')
        for chat_pk in chat_pks:
            chat = Chat.objects.get(pk=chat_pk)
            today = datetime.now()
            profiles = Profile.objects.filter(
                chats=chat,
                birthday__day=today.day,
                birthday__month=today.month
            )

            for profile in profiles:
                gamer = Gamer.objects.filter(profile=profile).first()
                if gamer:
                    gamer.roulette_points += 100000
                    gamer.save()
                    if profile.celebrate_bday:
                        rmi1 = ResponseMessageItem(f"С Днём рождения, {tg_bot.get_mention(profile)}!",
                                                   peer_id=chat.chat_id)
                        rmi2 = ResponseMessageItem("На ваш счет зачислено 100 000 бонусных очков.",
                                                   peer_id=chat.chat_id)
                        rm = ResponseMessage([rmi1, rmi2])
                        tg_bot.send_response_message(rm)

    def add_arguments(self, parser):
        parser.add_argument('chat_id', nargs='+', type=str, help='chat_id')
