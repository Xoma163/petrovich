import datetime
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.DoTheLinuxComand import do_the_linux_command


class RedditSaver:
    CONTENT_TYPE_RICH_VIDEO = "rich:video"
    CONTENT_TYPE_VIDEO = "hosted:video"
    CONTENT_TYPE_IMAGE = "image"
    CONTENT_TYPE_IMAGES = "images"
    CONTENT_TYPE_TEXT = "self"
    CONTENT_TYPE_LINK = "link"

    def __init__(self):
        self.timestamp = datetime.datetime.now().timestamp()
        self.tmp_video_file = NamedTemporaryFile()
        self.tmp_audio_file = NamedTemporaryFile()
        self.tmp_output_file = NamedTemporaryFile()
        self.title = None
        self.data = None
        self.media_data = None
        self.post_url = None
        self.content_type = None

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
        video_url = None

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

    def _get_download_video_and_audio(self, video_url, audio_url):
        do_the_linux_command(f"curl -o {self.tmp_video_file.name} {video_url}")
        do_the_linux_command(f"curl -o {self.tmp_audio_file.name} {audio_url}")

    def _mux_video_and_audio(self):
        try:
            do_the_linux_command(
                f"ffmpeg -i {self.tmp_video_file.name} -i {self.tmp_audio_file.name} -c:v copy -c:a aac -strict experimental -f mp4 -y {self.tmp_output_file.name}")
        finally:
            self._delete_video_audio_files()

    def _delete_video_audio_files(self):
        self.tmp_video_file.close()
        self.tmp_audio_file.close()

    def _delete_output_file(self):
        self.tmp_output_file.close()

    def _get_video_bytes(self):
        try:
            with open(self.tmp_output_file.name, 'rb') as file:
                file_bytes = file.read()
        finally:
            self._delete_output_file()
        return file_bytes

    def get_video_from_post(self) -> bytes:
        """
        Получаем видео с аудио
        """

        video_url, audio_url = self._get_reddit_video_audio_urls()
        # Нет нужды делать временные файлы для джоина видео и аудио, если аудио нет, то просто кидаем видео и всё
        if not audio_url:
            return video_url
            # return requests.get(video_url).content
        self._get_download_video_and_audio(video_url, audio_url)
        self._mux_video_and_audio()
        return self._get_video_bytes()

    def get_text_from_post(self):
        return self.data['selftext']

    def get_link_from_post(self):
        return self.data['url_overridden_by_dest']

    def get_photo_from_post(self):
        return self.data['url_overridden_by_dest']

    def get_photos_from_post(self):
        gallery_data_items = self.data['gallery_data']['items']
        # Чёрная магия
        return [
            self.data["media_metadata"][x["media_id"]]["s"]["u"].partition("?")[0].replace("/preview.", "/i.", 1)
            for x in gallery_data_items
        ]

    def get_from_reddit(self, post_url):
        self.set_post_url(post_url)
        self.get_post_data()

        if self.is_video:
            return self.get_video_from_post()
        elif self.is_image:
            return self.get_photo_from_post()
        elif self.is_images:
            return self.get_photos_from_post()
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
            'From': 'testyouremail@domain.com'
        }
        url = self.post_url + ".json"
        data = requests.get(url, headers=headers).json()
        self.data = data[0]["data"]["children"][0]["data"]
        self.title = self.data['title']
        self.media_data = self.data["media"]
        self.content_type = self.data.get('post_hint', self.CONTENT_TYPE_TEXT)

        if not self.media_data:
            if 'crosspost_parent_list' in self.data:
                self.data = self.data['crosspost_parent_list'][0]
                self.media_data = data["media"]

    def set_post_url(self, post_url):
        parsed_url = urlparse(post_url)
        self.post_url = f"{parsed_url.scheme}://{parsed_url.hostname}{parsed_url.path}"

    @property
    def is_video(self):
        return self.content_type in [self.CONTENT_TYPE_VIDEO, self.CONTENT_TYPE_RICH_VIDEO]

    @property
    def is_image(self):
        return self.content_type == self.CONTENT_TYPE_IMAGE

    @property
    def is_images(self):
        return self.content_type == self.CONTENT_TYPE_IMAGES

    @property
    def is_text(self):
        return self.content_type == self.CONTENT_TYPE_TEXT

    @property
    def is_link(self):
        return self.content_type == self.CONTENT_TYPE_LINK
