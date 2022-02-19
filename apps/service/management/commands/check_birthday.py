from datetime import datetime

from django.core.management.base import BaseCommand

from apps.bot.classes.bots.tg.TgBot import TgBot
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
                        tg_bot.parse_and_send_msgs(
                            [
                                f"С Днём рождения, {tg_bot.get_mention(profile)}!",
                                "На ваш счет зачислено 100 000 бонусных очков."
                            ],
                            chat.chat_id
                        )

    def add_arguments(self, parser):
        parser.add_argument('chat_id', nargs='+', type=str, help='chat_id')
