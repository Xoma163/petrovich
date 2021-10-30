from django.core.management import BaseCommand

from apps.bot.APIs.YoutubeLiveCheckerAPI import YoutubeLiveCheckerAPI
from apps.bot.classes.bots.Bot import get_bot_by_platform
from apps.bot.classes.consts.Consts import Platform
from apps.bot.models import Chat
from apps.service.models import Service


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('chat_id', nargs='+', type=str, help='chat_id')

    def handle(self, *args, **options):
        chat_pks = options['chat_id'][0].split(',')

        ylc_api = YoutubeLiveCheckerAPI()
        livestream_info = ylc_api.get_stream_info_if_online()
        if not livestream_info:
            return

        stream, _ = Service.objects.get_or_create(name="stream")
        if stream.value == livestream_info['video_url']:
            return

        stream.value = livestream_info['video_url']
        stream.save()

        for chat_pk in chat_pks:
            chat = Chat.objects.get(pk=chat_pk)
            bot = get_bot_by_platform(chat.get_platform_enum())
            if bot.platform == Platform.TG:
                msg = {'text': f"Ктап подрубил [Стрим]({stream.value})", 'parse_mode': 'markdown'}
            else:
                msg = f"Ктап подрубил стрим\n{stream.value}"
            bot.parse_and_send_msgs(msg, chat.chat_id)
