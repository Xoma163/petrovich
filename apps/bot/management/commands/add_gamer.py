from datetime import datetime

from django.core.management.base import BaseCommand

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.models import Chat, Profile

tg_bot = TgBot()


class Command(BaseCommand):
    def handle(self, *args, **options):
        bday_chats = Chat.objects.filter(settings__celebrate_bday=True)

        today = datetime.now()
        profiles = Profile.objects.filter(
            birthday__day=today.day,
            birthday__month=today.month
        )
        for profile in profiles:
            profile.gamer.roulette_points += 100000
            profile.gamer.save()
            if not profile.settings.celebrate_bday:
                continue

            rmi = ResponseMessageItem(
                f"С Днём рождения, {tg_bot.get_mention(profile)}!",
                peer_id=profile.get_tg_user().user_id
            )
            rm = ResponseMessage(rmi)
            tg_bot.send_response_message(rm)

            bday_chats = profile.chats.filter(pk__in=[x.pk for x in bday_chats])
            for chat in bday_chats:
                rmi1 = ResponseMessageItem(
                    f"С Днём рождения, {tg_bot.get_mention(profile)}!",
                    peer_id=chat.chat_id
                )
                rm = ResponseMessage(rmi1)
                tg_bot.send_response_message(rm)
