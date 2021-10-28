import time

from django.core.management import BaseCommand

from apps.bot.APIs.YoutubeInfo import YoutubeInfo
from apps.bot.classes.bots.Bot import get_bot_by_platform
from apps.service.models import YoutubeSubscribe


class Command(BaseCommand):

    def __init__(self):
        super().__init__()

    def handle(self, *args, **kwargs):
        yt_subs = YoutubeSubscribe.objects.all()
        for yt_sub in yt_subs:
            youtube_info = YoutubeInfo(yt_sub.channel_id)
            youtube_data = youtube_info.get_youtube_channel_info()
            if youtube_data['last_video']['date'] > yt_sub.date:
                if yt_sub.chat:
                    bot = get_bot_by_platform(yt_sub.chat.get_platform_enum())
                    peer_id = yt_sub.chat.chat_id
                else:
                    bot = get_bot_by_platform(yt_sub.author.get_platform_enum())
                    peer_id = yt_sub.author.user_id
                msg = f"Новое видео на канале {yt_sub.title}\n" \
                      f"{youtube_data['last_video']['title']}\n" \
                      f"{youtube_data['last_video']['link']}"

                res = {'text': msg, 'attachments': [youtube_data['last_video']['link']]}
                bot.parse_and_send_msgs(peer_id, res)
                yt_sub.date = youtube_data['last_video']['date']
                yt_sub.save()
            time.sleep(2)
