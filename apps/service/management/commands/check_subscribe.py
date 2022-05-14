import time

import requests
from bs4 import BeautifulSoup
from django.core.management import BaseCommand

from apps.bot.APIs.YoutubeInfo import YoutubeInfo
from apps.bot.classes.bots.Bot import get_bot_by_platform
from apps.bot.classes.consts.Consts import Platform
from apps.bot.utils.utils import get_tg_formatted_url
from apps.service.models import Subscribe


class Command(BaseCommand):

    def __init__(self):
        super().__init__()

    def handle(self, *args, **kwargs):
        subs = Subscribe.objects.all()
        for sub in subs:
            if sub.service == Subscribe.SERVICE_YOUTUBE:
                pass
                # self.check_youtube_video(sub)
            elif sub.service == Subscribe.SERVICE_THE_HOLE:
                self.check_the_hole_video(sub)

    def check_youtube_video(self, sub):
        youtube_info = YoutubeInfo(sub.channel_id)
        youtube_data = youtube_info.get_youtube_last_video()
        if not youtube_data['last_video']['date'] > sub.date:
            return
        title = youtube_data['last_video']['title']
        link = youtube_data['last_video']['link']
        self.send_notify(sub, title, link)

        sub.date = youtube_data['last_video']['date']
        sub.save()
        time.sleep(2)

    def check_the_hole_video(self, sub):
        content = requests.get(f"https://the-hole.tv/shows/{sub.channel_id}").content
        bs4 = BeautifulSoup(content, 'html.parser')
        last_videos = [x.attrs['href'] for x in bs4.select('a[href*=episodes]')]
        titles = [x.nextSibling.nextSibling.text for x in bs4.select('a[href*=episodes]')]
        last_video_id = sub.last_video_id
        new_videos = last_videos[0:last_videos.index(last_video_id)]

        for i, new_video in enumerate(new_videos):
            title = titles[i]
            link = f"https://the-hole.tv/{new_video}"
            self.send_notify(sub, title, link)
        sub.last_video_id = last_videos[0]
        sub.save()

    @staticmethod
    def send_notify(sub, title, link):
        bot = get_bot_by_platform(sub.author.get_platform_enum())

        if bot.platform == Platform.TG:
            text = f"Новое видео на канале {sub.title}\n" \
                   f"{get_tg_formatted_url(title, link)}"
        else:
            text = f"Новое видео на канале {sub.title}\n" \
                   f"{title}\n" \
                   f"{link}"

        bot.parse_and_send_msgs(text, sub.peer_id)
