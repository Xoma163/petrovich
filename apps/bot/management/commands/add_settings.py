from django.core.management.base import BaseCommand

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.models import Profile, UserSettings, Chat, ChatSettings

tg_bot = TgBot()


class Command(BaseCommand):

    def handle(self, *args, **options):
        for profile in Profile.objects.all():
            us = UserSettings()
            us.celebrate_bday = profile.celebrate_bday
            us.show_birthday_year = profile.show_birthday_year
            us.gpt_preprompt = profile.gpt_preprompt
            us.save()

            profile.settings = us
            profile.save()

        for chat in Chat.objects.all():
            cs = ChatSettings()
            cs.need_reaction = chat.need_reaction
            cs.mentioning = chat.mentioning
            cs.need_meme = chat.need_meme
            cs.recognize_voice = chat.recognize_voice
            cs.need_turett = chat.need_turett
            cs.use_swear = chat.use_swear
            cs.gpt_preprompt = chat.gpt_preprompt
            cs.save()

            chat.settings = cs
            chat.save()
