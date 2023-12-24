from django.core.management.base import BaseCommand

from apps.bot.classes.bots.tg_bot import TgBot
from apps.service.models import Subscribe

tg_bot = TgBot()


class Command(BaseCommand):

    def handle(self, *args, **options):
        subs = Subscribe.objects.all()
        for sub in subs:
            sub.last_videos_id = [sub.last_video_id]
            sub.save()
