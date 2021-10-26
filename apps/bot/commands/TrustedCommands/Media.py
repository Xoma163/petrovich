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
            YOUTUBE_URLS: self.get_youtube_video_info,
            TIKTOK_URLS: self.get_tiktok_video_info,
            REDDIT_URLS: self.get_reddit_video_info,
            INSTAGRAM_URLS: self.get_instagram_video_info
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

        self.bot.set_activity(self.event.peer_id, ActivitiesEnum.UPLOAD_VIDEO)
        try:
            video, title = method(chosen_url)
        except PWarning as e:
            # Если была вызвана команда или отправлено сообщение в лс
            if has_command_name or self.event.is_from_pm:
                raise e
            else:
                return
        self.bot.set_activity(self.event.peer_id, ActivitiesEnum.UPLOAD_VIDEO)
        attachments = [self.bot.upload_video(video)]

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
            text += f"От пользователя {self.event.sender}\n" \
                    f"{chosen_url}"
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

        # Ебучий тикток отдаёт контект ИНОГДА, поэтому такой костыль с пересозданием сессии
        tries = 10
        s = requests.Session()
        video_data = None
        for _ in range(tries):
            r = s.get(url, headers=headers)
            bs4 = BeautifulSoup(r.content, 'html.parser')
            try:
                video_data = json.loads(bs4.find(id='__NEXT_DATA__').contents[0])
                break
            except (AttributeError, ConnectionError):
                s = requests.Session()
        if not video_data:
            raise RuntimeError("Ошибка загрузки видео с tiktok")

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
        try:
            content_type = bs4.find('meta', attrs={'name': 'medium'}).attrs['content']
        except Exception:
            raise PWarning("Ссылка на инстаграмм не является видео")
        if content_type != 'video':
            raise PWarning("Ссылка на инстаграмм не является видео")
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
