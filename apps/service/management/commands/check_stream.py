from django.core.management import BaseCommand

from apps.bot.APIs.YoutubeAPI import YoutubeAPI
from apps.bot.classes.bots.Bot import get_bot_by_platform
from apps.bot.classes.consts.Consts import Platform
from apps.bot.models import Chat
from apps.bot.utils.utils import get_tg_formatted_url
from apps.service.models import Service


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('chat_id', nargs='+', type=str, help='chat_id')

    def handle(self, *args, **options):
        chat_pks = options['chat_id'][0].split(',')

        y_api = YoutubeAPI()
        livestream_info = y_api.get_stream_info_if_online()
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
            url = stream.value
            if bot.platform == Platform.TG:
                text = get_tg_formatted_url("стрим", url)
            else:
                text = f"Ктап подрубил стрим\n{url}"
            bot.parse_and_send_msgs(text, chat.chat_id)
