from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.utils.utils import get_url_file_ext, get_default_headers
from apps.bot.utils.video.video_handler import VideoHandler


class Reddit:
    CONTENT_TYPE_RICH_VIDEO = "rich:video"
    CONTENT_TYPE_VIDEO = "hosted:video"
    CONTENT_TYPE_IMAGE = "image"
    CONTENT_TYPE_IMAGES = "images"
    CONTENT_TYPE_TEXT = "self"
    CONTENT_TYPE_LINK = "link"

    def __init__(self):
        self.title = None
        self.data = None
        self.media_data = None
        self.post_url = None
        self.content_type = None

        self.filename = None

    @staticmethod
    def _parse_mpd_audio_filename(url) -> str | None:
        """
        Достаём имя файла на сервере реддита. Если его нет, то по умолчанию это "audio"
        Если нашли имя файла, то также проставляем формат файла
        """
        xml = requests.get(url).content
        bs4 = BeautifulSoup(xml, 'html.parser')
        try:
            filename = bs4.find("adaptationset", {
                'contenttype': 'audio'
            }).find('representation').find('baseurl').text
            return filename
        except Exception:
            try:
                filename = bs4.find("representation", {
                    'id': 'AUDIO-1'
                }).find('baseurl').text
                return filename
            except Exception:
                return None

    def _get_reddit_video_audio_urls(self) -> tuple[str, str]:
        audio_url = None

        if self.media_data and self.media_data.get('type') == 'gfycat.com':
            video_url = self.media_data['oembed']['thumbnail_url'].replace('size_restricted.gif', 'mobile.mp4')
        elif self.media_data and "reddit_video" in self.media_data:
            video_url = self.media_data["reddit_video"]["fallback_url"]
            audio_filename = self._parse_mpd_audio_filename(self.media_data['reddit_video']['dash_url'])
            if audio_filename:
                audio_url = video_url.split("DASH_")[0] + audio_filename
        elif self.data.get('url_overridden_by_dest'):
            video_url = self.data['url_overridden_by_dest']
        else:
            raise PWarning("Нет видео в посте")
        return video_url, audio_url

    def _get_video_from_post(self):
        """
        Получаем видео с аудио
        """

        video_url, audio_url = self._get_reddit_video_audio_urls()
        ext = get_url_file_ext(video_url)
        self.filename = f"{self.title.replace(' ', '_')}.{ext}"
        # Нет нужды делать временные файлы для джоина видео и аудио, если аудио нет, то просто кидаем видео и всё
        if not audio_url:
            return video_url

        va = VideoAttachment()
        va.public_download_url = video_url
        va.download_content(stream=True)

        aa = AudioAttachment()
        aa.public_download_url = audio_url
        aa.download_content(stream=True)

        vh = VideoHandler(video=va, audio=aa)
        return vh.mux()

    def _get_text_from_post(self) -> str:
        return self.data['selftext']

    def _get_link_from_post(self) -> str:
        return self.data['url_overridden_by_dest']

    def _get_photo_from_post(self) -> str:
        photo_url = self.data['url_overridden_by_dest']
        ext = get_url_file_ext(photo_url)

        self.filename = f"{self.title.replace(' ', '_')}.{ext}"
        return photo_url

    def _get_photos_from_post(self) -> list[str]:
        gallery_data_items = self.data['gallery_data']['items']
        first_url = \
            self.data["media_metadata"][self.data['gallery_data']['items'][0]["media_id"]]["s"]["u"].partition("?")[0]
        ext = get_url_file_ext(first_url)
        self.filename = f"{self.title.replace(' ', '_')}.{ext}"

        # Чёрная магия
        return [
            self.data["media_metadata"][x["media_id"]]["s"]["u"].partition("?")[0].replace("/preview.", "/i.", 1)
            for x in gallery_data_items
        ]

    def get_post_data(self, post_url):
        self._set_post_url(post_url)
        self._get_post_data()

        if self.is_gallery:
            return self._get_photos_from_post()
        elif self.is_image:
            return [self._get_photo_from_post()]
        elif self.is_images:
            return self._get_photos_from_post()
        elif self.is_video or self.is_gif:
            return self._get_video_from_post()
        elif self.is_text:
            return self._get_text_from_post()
        elif self.is_link:
            link = self._get_link_from_post()
            formats = ["gif", "webm", "mp4"]
            if any([link.endswith(x) for x in formats]):
                self.content_type = self.CONTENT_TYPE_VIDEO
                return self._get_video_from_post()
            return link

    def _get_post_data(self):
        # use UA headers to prevent 429 error
        headers = get_default_headers()
        try:
            post_url = requests.get(self.post_url, headers=headers).history[-1].url
            self.post_url = post_url
        except:
            pass
        urlparsed = urlparse(self.post_url)
        url = f"{urlparsed.scheme}://{urlparsed.netloc}{urlparsed.path}.json"
        data = requests.get(url, headers=headers).json()

        self.data = data[0]["data"]["children"][0]["data"]
        self.title = self.data['title']
        self.media_data = self.data["media"]
        self.content_type = self.data.get('post_hint', self.CONTENT_TYPE_TEXT)

        if not self.media_data:
            if self.data.get('media'):
                self.media_data = self.data["media"]
            elif 'crosspost_parent_list' in self.data:
                self.data = self.data['crosspost_parent_list'][0]
                if isinstance(data, dict):
                    self.media_data = data["media"]
                else:
                    self.media_data = self.data['media']

    def _set_post_url(self, post_url: str):
        parsed_url = urlparse(post_url)
        self.post_url = f"{parsed_url.scheme}://{parsed_url.hostname}{parsed_url.path}"

    @property
    def is_gallery(self):
        return self.data.get('is_gallery', False)

    @property
    def is_video(self):
        if self.media_data and 'reddit_video' in self.media_data or self.data.get('url_overridden_by_dest'):
            return True
        return self.content_type in [self.CONTENT_TYPE_VIDEO, self.CONTENT_TYPE_RICH_VIDEO]

    @property
    def is_gif(self):
        url = self.data.get('url_overridden_by_dest')
        if url and (url.endswith('.gif') or url.endswith(".gifv")):
            return True
        return False

    @property
    def is_image(self):
        return self.content_type == self.CONTENT_TYPE_IMAGE and not self.data.get('url_overridden_by_dest').endswith(
            '.gif')

    @property
    def is_images(self):
        return self.content_type == self.CONTENT_TYPE_IMAGES

    @property
    def is_text(self):
        return self.content_type == self.CONTENT_TYPE_TEXT

    @property
    def is_link(self):
        return self.content_type == self.CONTENT_TYPE_LINK
