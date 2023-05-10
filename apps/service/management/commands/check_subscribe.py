import logging
import time

from django.core.management import BaseCommand

from apps.bot.APIs.TheHoleAPI import TheHoleAPI
from apps.bot.APIs.WASDAPI import WASDAPI
from apps.bot.APIs.YoutubeVideoAPI import YoutubeVideoAPI
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.events.Event import Event
from apps.bot.commands.Media import Media
from apps.bot.utils.utils import get_tg_formatted_url
from apps.service.models import Subscribe

logger = logging.getLogger('subscribe_notifier')


class Command(BaseCommand):

    def __init__(self):
        super().__init__()

    def handle(self, *args, **kwargs):
        subs = Subscribe.objects.all()
        for sub in subs:
            try:
                self.check_sub(sub)
            except Exception as e:
                logger.exception("Ошибка в проверке/отправке оповещения о стриме")

    def check_sub(self, sub):
        if sub.service == Subscribe.SERVICE_YOUTUBE:
            self.check_youtube_video(sub)
        elif sub.service == Subscribe.SERVICE_THE_HOLE:
            self.check_the_hole_video(sub)
        elif sub.service == Subscribe.SERVICE_WASD:
            self.check_wasd_video(sub)

    def check_youtube_video(self, sub):
        youtube_info = YoutubeVideoAPI()
        youtube_data = youtube_info.get_last_video(sub.channel_id)
        if not youtube_data['last_video']['date'] > sub.date:
            return
        is_shorts = youtube_data['last_video']['is_shorts']
        if sub.youtube_ignore_shorts and is_shorts:
            sub.date = youtube_data['last_video']['date']
            sub.save()
            return
        title = youtube_data['last_video']['title']
        link = youtube_data['last_video']['link']
        self.send_notify(sub, title, link)

        sub.date = youtube_data['last_video']['date']
        sub.save()
        time.sleep(2)

    def check_the_hole_video(self, sub):
        th_api = TheHoleAPI()
        last_videos, titles = th_api.get_last_videos_with_titles(sub.channel_id)
        last_video_id = sub.last_video_id
        new_videos = last_videos[0:last_videos.index(last_video_id)]
        new_videos = list(reversed(new_videos))

        for i, new_video in enumerate(new_videos):
            title = titles[i]
            link = f"{th_api.URL}{new_video}"
            self.send_notify(sub, title, link)
            self.send_the_hole_file(sub, link)
        sub.last_video_id = last_videos[0]
        sub.save()

    def check_wasd_video(self, sub):
        wasd = WASDAPI()
        channel_is_live = wasd.channel_is_live(sub.title)
        if not channel_is_live or sub.last_stream_status:
            sub.last_stream_status = channel_is_live
            sub.save()
            return

        link = f"{wasd.URL}{sub.title}"
        self.send_notify(sub, wasd.title, link, is_stream=True)

        sub.last_stream_status = channel_is_live
        sub.save()

    @staticmethod
    def send_notify(sub, title, link, is_stream=False):
        bot = TgBot()

        new_video_text = "Новое видео" if not is_stream else "Стрим"

        if bot.platform == Platform.TG:
            text = f"{new_video_text} на канале {sub.title}\n" \
                   f"{get_tg_formatted_url(title, link)}"
        else:
            text = f"{new_video_text} на канале {sub.title}\n" \
                   f"{title}\n" \
                   f"{link}"
        logger.info(f"Отправил уведомление по подписке с id={sub.pk}")
        # ToDo: check message_thread_id
        bot.parse_and_send_msgs(text, sub.peer_id, sub.message_thread_id)

    @staticmethod
    def send_the_hole_file(sub, link):
        bot = TgBot()
        event = Event(bot=bot, peer_id=sub.peer_id)

        media_command = Media(bot, event)
        att, title = media_command.get_the_hole_video(link)
        # ToDo: check message_thread_id
        msg = {'text': title, 'attachments': att}
        bot.parse_and_send_msgs(msg, sub.peer_id, sub.message_thread_id)
