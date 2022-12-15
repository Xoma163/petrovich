from django.core.management import BaseCommand
from django.db.models import Q

from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.consts.Exceptions import PSkip
from apps.bot.classes.events.TgEvent import TgEvent
from apps.bot.commands.Meme import Meme as MemeCommand
from apps.service.models import Meme


class Command(BaseCommand):

    def __init__(self):
        super().__init__()

    def handle(self, *args, **kwargs):
        q = Q(approved=True) & (Q(type='link', link__icontains="youtu"))
        memes = Meme.objects.filter(q)
        tg_bot = TgBot()
        event = TgEvent(bot=tg_bot)
        event.peer_id = 120712437
        mc = MemeCommand(tg_bot, event)
        for meme in memes:
            try:
                mc.prepare_meme_to_send(meme)
            except PSkip:
                pass
            except Exception as e:
                print(e)
