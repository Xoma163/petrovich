from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from apps.bot.classes.const.exceptions import PWarning
from apps.bot.utils.audio_video_muxer import AudioVideoMuxer
from apps.bot.utils.utils import get_url_file_ext


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
    def _parse_mpd_audio_filename(url):
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

    def _get_reddit_video_audio_urls(self):
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

    def get_video_from_post(self) -> bytes:
        """
        Получаем видео с аудио
        """

        video_url, audio_url = self._get_reddit_video_audio_urls()
        ext = get_url_file_ext(video_url)
        self.filename = f"{self.title.replace(' ', '_')}.{ext}"
        # Нет нужды делать временные файлы для джоина видео и аудио, если аудио нет, то просто кидаем видео и всё
        if not audio_url:
            return video_url
            # return requests.get(video_url).content
        avm = AudioVideoMuxer()
        video_content = requests.get(video_url).content
        audio_content = requests.get(audio_url).content
        video = avm.mux(video_content, audio_content)
        return video

    def get_text_from_post(self):
        return self.data['selftext']

    def get_link_from_post(self):
        return self.data['url_overridden_by_dest']

    def get_photo_from_post(self):
        photo_url = self.data['url_overridden_by_dest']
        ext = get_url_file_ext(photo_url)

        self.filename = f"{self.title.replace(' ', '_')}.{ext}"
        return photo_url

    def get_photos_from_post(self):
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

    def get_from_reddit(self, post_url):
        self.set_post_url(post_url)
        self.get_post_data()

        if self.is_gallery:
            return self.get_photos_from_post()
        elif self.is_image:
            return [self.get_photo_from_post()]
        elif self.is_images:
            return self.get_photos_from_post()
        elif self.is_video or self.is_gif:
            return self.get_video_from_post()
        elif self.is_text:
            return self.get_text_from_post()
        elif self.is_link:
            link = self.get_link_from_post()
            formats = ["gif", "webm", "mp4"]
            if any([link.endswith(x) for x in formats]):
                self.content_type = self.CONTENT_TYPE_VIDEO
                return self.get_video_from_post()
            return link

    def get_post_data(self):
        # use UA headers to prevent 429 error
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36 OPR/38.0.2220.41',
            # 'From': 'testyouremail@domain.com'
        }
        post_url = requests.get(self.post_url, headers=headers).history[-1].url
        self.post_url = post_url
        urlparsed = urlparse(post_url)

        url = f"{urlparsed.scheme}://{urlparsed.netloc}{urlparsed.path}.json"
        data = requests.get(url, headers=headers).json()
        self.data = data[0]["data"]["children"][0]["data"]
        self.title = self.data['title']
        self.media_data = self.data["media"]
        self.content_type = self.data.get('post_hint', self.CONTENT_TYPE_TEXT)

        # ToDo: unchecked
        if not self.media_data:
            if self.data.get('media'):
                self.media_data = self.data["media"]
            elif 'crosspost_parent_list' in self.data:
                self.data = self.data['crosspost_parent_list'][0]
                if isinstance(data, dict):
                    self.media_data = data["media"]
                else:
                    self.media_data = self.data['media']

    def set_post_url(self, post_url):
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
