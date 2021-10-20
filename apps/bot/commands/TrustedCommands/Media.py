import json
from urllib.parse import urlparse

import requests
import youtube_dl
from bs4 import BeautifulSoup

from apps.bot.APIs.RedditVideoDownloader import RedditVideoSaver
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PWarning

YOUTUBE_URLS = ['www.youtube.com', 'youtube.com', "www.youtu.be", "youtu.be"]
REDDIT_URLS = ["www.reddit.com"]
TIKTOK_URLS = ["www.tiktok.com", 'vm.tiktok.com', 'm.tiktok.com']
INSTAGRAM_URLS = ['www.instagram.com', 'instagram.com']

MEDIA_URLS = YOUTUBE_URLS + REDDIT_URLS + TIKTOK_URLS + INSTAGRAM_URLS


class Media(Command):
    name = "медиа"
    help_text = "скачивает видео из Reddit/TikTok/YouTube/Instagram и присылает его"
    help_texts = [
        "(ссылка на видео) - скачивает видео из Reddit/TikTok/YouTube/Instagram и присылает его"
    ]
    platforms = [Platform.TG]

    def start(self):
        MEDIA_TRANSLATOR = {
            'youtube': self.get_youtube_video_info,
            'tiktok': self.get_tiktok_video_info,
            'reddit': self.get_reddit_video_info,
            'instagram': self.get_instagram_video_info
        }

        if self.event.message.command in self.full_names:
            if self.event.message.args:
                url = self.event.message.args[0]
            elif self.event.fwd:
                url = self.event.fwd[0]['text']
            else:
                raise PWarning("Для работы команды требуются аргументы или пересылаемые сообщения")
        else:
            url = self.event.message.raw

        media_link_is_from = None

        if urlparse(url).hostname in YOUTUBE_URLS:
            media_link_is_from = 'youtube'
        if urlparse(url).hostname in TIKTOK_URLS:
            media_link_is_from = 'tiktok'
        if urlparse(url).hostname in REDDIT_URLS:
            media_link_is_from = 'reddit'
        if urlparse(url).hostname in INSTAGRAM_URLS:
            media_link_is_from = 'instagram'

        if not media_link_is_from:
            raise PWarning("Не youtube/tiktok/reddit/instagram ссылка")

        self.bot.set_activity(self.event.peer_id, ActivitiesEnum.UPLOAD_VIDEO)
        video, title = MEDIA_TRANSLATOR[media_link_is_from](url)
        self.bot.set_activity(self.event.peer_id, ActivitiesEnum.UPLOAD_VIDEO)
        attachments = [self.bot.upload_video(video)]

        if self.event.message.command not in self.full_names:
            self.bot.delete_message(self.event.peer_id, self.event.message.id)

            text = ""
            if title:
                text = f"{title}\n"
            text += f"От пользователя {self.event.sender}\n" \
                    f"{url}"
            return {'text': text, 'attachments': attachments}
        else:
            return {'attachments': attachments}

    @staticmethod
    def get_youtube_video_info(url):
        ydl_params = {
            'outtmpl': '%(id)s%(ext)s',
            'logger': NothingLogger()
        }
        ydl = youtube_dl.YoutubeDL(ydl_params)
        ydl.add_default_info_extractors()

        try:
            video_info = ydl.extract_info(url, download=False)
        except youtube_dl.utils.DownloadError:
            raise PWarning("Не смог найти видео по этой ссылке")
        video_urls = []
        if video_info['duration'] > 60:
            raise PWarning("Нельзя грузить видосы > 60 секунд с ютуба")
        if 'formats' in video_info:
            for _format in video_info['formats']:
                if _format['ext'] == 'mp4' and _format['asr']:
                    video_urls.append(_format)

        if len(video_urls) == 0:
            raise PWarning("Чёт проблемки, напишите разрабу и пришли ссылку на видео")
        max_quality_video = sorted(video_urls, key=lambda x: x['format_note'])[0]
        url = max_quality_video['url']
        video_content = requests.get(url).content
        return video_content, video_info['title']

    @staticmethod
    def get_tiktok_video_info(url):
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        s = requests.Session()
        r = s.get(url, headers=headers)
        bs4 = BeautifulSoup(r.content, 'html.parser')
        video_data = json.loads(bs4.find(id='__NEXT_DATA__').contents[0])

        item_struct = video_data['props']['pageProps']['itemInfo']['itemStruct']
        video_url = item_struct['video']['downloadAddr']
        title = item_struct['desc']
        headers['Referer'] = video_data['props']['pageProps']['seoProps']['metaParams']['canonicalHref']
        r = s.get(video_url, headers=headers)
        s.close()
        return r.content, title

    @staticmethod
    def get_reddit_video_info(url):
        rvs = RedditVideoSaver()
        video = rvs.get_video_from_post(url)
        return video, rvs.title

    @staticmethod
    def get_instagram_video_info(url):
        r = requests.get(url)
        bs4 = BeautifulSoup(r.content, 'html.parser')
        content_type = bs4.find('meta', attrs={'name': 'medium'}).attrs['content']
        if content_type != 'video':
            raise PWarning("Ссылка на инстаграм не является видео")
        video_url = bs4.find('meta', attrs={'property': 'og:video'}).attrs['content']
        return video_url, ""


class NothingLogger(object):
    @staticmethod
    def debug(msg):
        pass

    @staticmethod
    def warning(msg):
        pass

    @staticmethod
    def error(msg):
        print(msg)
