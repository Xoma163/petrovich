import json
from urllib.parse import urlparse

import requests
import youtube_dl
from bs4 import BeautifulSoup

from apps.bot.APIs.RedditVideoDownloader import RedditVideoSaver
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PWarning, PSkip
from apps.bot.utils.utils import get_urls_from_text

YOUTUBE_URLS = ('www.youtube.com', 'youtube.com', "www.youtu.be", "youtu.be")
REDDIT_URLS = ("www.reddit.com",)
TIKTOK_URLS = ("www.tiktok.com", 'vm.tiktok.com', 'm.tiktok.com')
INSTAGRAM_URLS = ('www.instagram.com', 'instagram.com')

MEDIA_URLS = tuple(list(YOUTUBE_URLS) + list(REDDIT_URLS) + list(TIKTOK_URLS) + list(INSTAGRAM_URLS))


class Media(Command):
    name = "медиа"
    help_text = "скачивает видео из Reddit/TikTok/YouTube/Instagram и присылает его"
    help_texts = [
        "(ссылка на видео) - скачивает видео из Reddit/TikTok/YouTube/Instagram и присылает его"
    ]
    platforms = [Platform.TG]

    def __init__(self):
        super().__init__()
        self.MEDIA_TRANSLATOR = {
            YOUTUBE_URLS: self.get_youtube_video,
            TIKTOK_URLS: self.get_tiktok_video,
            REDDIT_URLS: self.get_reddit_attachment,
            INSTAGRAM_URLS: self.get_instagram_attachment,
        }

    def start(self):

        if self.event.message.command in self.full_names:
            if self.event.message.args:
                source = self.event.message.args_case[0]
            elif self.event.fwd:
                source = self.event.fwd[0].message.raw
            else:
                raise PWarning("Для работы команды требуются аргументы или пересылаемые сообщения")
            has_command_name = True
        else:
            source = self.event.message.raw
            has_command_name = False

        method, chosen_url = self.get_method_and_chosen_url(source)

        try:
            attachments, title = method(chosen_url)
        except PWarning as e:
            # Если была вызвана команда или отправлено сообщение в лс
            if has_command_name or self.event.is_from_pm:
                raise e
            else:
                raise PSkip()

        if has_command_name or self.event.is_from_pm:
            return {'attachments': attachments}
        else:
            self.bot.delete_message(self.event.peer_id, self.event.message.id)
            chosen_url_pos = source.find(chosen_url)
            extra_text = source[:chosen_url_pos].strip() + "\n" + source[chosen_url_pos + len(chosen_url):].strip()
            extra_text = extra_text.strip()

            text = ""
            if title:
                text = f"{title}\n"
            text += f"От пользователя {self.event.sender}"

            if self.event.platform == Platform.TG:
                text += f"\n[Сурс]({chosen_url})"
            else:
                text += f"\n{chosen_url}"
            # Костыль, чтобы видосы которые шарятся с мобилы с реддита не дублировали title
            if extra_text and extra_text != title:
                text += f"\n{extra_text}"
            return {'text': text, 'attachments': attachments}

    def get_method_and_chosen_url(self, source):
        method = None
        urls = get_urls_from_text(source)
        for url in urls:
            hostname = urlparse(url).hostname
            if not hostname:
                raise PWarning("Не нашёл ссылки")
            for k in self.MEDIA_TRANSLATOR:
                if hostname in k:
                    return self.MEDIA_TRANSLATOR[k], url

        if not method:
            raise PWarning("Не youtube/tiktok/reddit/instagram ссылка")

    def get_youtube_video(self, url):
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
        attachments = [self.bot.upload_video(video_content, peer_id=self.event.peer_id)]
        return attachments, video_info['title']

    def get_tiktok_video(self, url):
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        content = requests.get(url, headers=headers).content
        bs4 = BeautifulSoup(content, 'html.parser')
        video_url = bs4.find('meta', attrs={'property': 'og:video'}).attrs['content']
        title = bs4.find('meta', attrs={'property': 'og:title'}).attrs['content']

        video = requests.get(video_url, headers=headers).content

        attachments = [self.bot.upload_video(video, peer_id=self.event.peer_id)]
        return attachments, title

    def get_reddit_attachment(self, url):
        rvs = RedditVideoSaver()
        video = rvs.get_video_from_post(url)
        attachments = [self.bot.upload_video(video, peer_id=self.event.peer_id)]
        return attachments, rvs.title

    def get_instagram_attachment(self, url):
        r = requests.get(url)
        bs4 = BeautifulSoup(r.content, 'html.parser')
        if 'reel' in url:
            content_type = 'reel'
        else:
            try:
                content_type = bs4.find('meta', attrs={'name': 'medium'}).attrs['content']
            except Exception:
                raise PWarning("Ссылка на инстаграмм не является видео/фото")

        if content_type == 'image':
            photo_url = bs4.find('meta', attrs={'property': 'og:image'}).attrs['content']
            return self.bot.upload_photos([photo_url], peer_id=self.event.peer_id), ""
        elif content_type == 'video':
            video_url = bs4.find('meta', attrs={'property': 'og:video'}).attrs['content']
            return [self.bot.upload_video(video_url, peer_id=self.event.peer_id)], ""
        elif content_type == 'reel':
            shared_data_text = "window._sharedData = "
            script_text = ";</script>"
            pos_start = r.text.find(shared_data_text)+len(shared_data_text)
            pos_end = r.text.find(script_text, pos_start)
            reel_data = json.loads(r.text[pos_start:pos_end])
            video_url = reel_data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['video_url']
            return [self.bot.upload_video(video_url, peer_id=self.event.peer_id)], ""
        else:
            raise PWarning("Ссылка на инстаграмм не является видео/фото")


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
