import time

from django.core.management import BaseCommand

from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.messages.ResponseMessage import ResponseMessage
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.models import Chat
from apps.service.models import Meme
from petrovich.settings import env


class Command(BaseCommand):
    def handle(self, *args, **options):

        photo_uploading_chat = Chat.objects.get(pk=env.str("TG_PHOTO_UPLOADING_CHAT_PK"))
        tg_bot = TgBot()
        memes = Meme.objects.filter(type='photo')
        len_memes = len(memes)
        for i, meme in enumerate(memes):
            msg = {}
            att = PhotoAttachment()
            att.file_id = meme.tg_file_id
            msg['attachments'] = att

            rm = ResponseMessage(msg, peer_id=photo_uploading_chat.chat_id)
            response = tg_bot.send_response_message_item(rm.messages[0])
            while response.status_code != 200:
                print('sleep')
                print(meme.pk)
                print(meme.name)
                time.sleep(1)
                response = tg_bot.send_response_message_item(rm.messages[0])
            print(f"{i}/{len_memes}")
