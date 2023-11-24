from django.core.management.base import BaseCommand

from apps.bot.classes.messages.attachments.link import LinkAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.service.models import Meme


class Command(BaseCommand):

    def handle(self, *args, **options):
        memes = Meme.objects.filter(type=LinkAttachment.TYPE)
        for meme in memes:
            link = LinkAttachment()
            if not meme.link:
                print("no meme link")
                print(meme.pk)
                continue
            link.url = meme.link

            if not meme.tg_file_id:
                print("no meme tg_file_id")
                print(meme.pk)
                continue

            meme.type = VideoAttachment.TYPE
            meme.save()
