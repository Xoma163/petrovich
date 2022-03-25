import datetime
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.DoTheLinuxComand import do_the_linux_command


class RedditVideoSaver:
    def __init__(self):
        self.timestamp = datetime.datetime.now().timestamp()
        self.tmp_video_file = NamedTemporaryFile()
        self.tmp_audio_file = NamedTemporaryFile()
        self.tmp_output_file = NamedTemporaryFile()
        self.title = None

    def parse_mpd_audio_filename(self, url):
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

    def get_reddit_video_audio_urls(self, post_url):
        # use UA headers to prevent 429 error
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36 OPR/38.0.2220.41',
            'From': 'testyouremail@domain.com'
        }
        url = post_url + ".json"
        data = requests.get(url, headers=headers).json()
        data = data[0]["data"]["children"][0]["data"]
        self.title = data['title']
        media_data = data["media"]
        if not media_data:
            if 'crosspost_parent_list' in data:
                data = data['crosspost_parent_list'][0]
                media_data = data["media"]

        audio_url = None
        video_url = None

        if media_data.get('type') == 'gfycat.com':
            video_url = media_data['oembed']['thumbnail_url'].replace('size_restricted.gif', 'mobile.mp4')
        elif "reddit_video" in media_data:
            video_url = media_data["reddit_video"]["fallback_url"]
            audio_filename = self.parse_mpd_audio_filename(media_data['reddit_video']['dash_url'])
            if audio_filename:
                audio_url = video_url.split("DASH_")[0] + audio_filename
        elif data.get('url_overridden_by_dest'):
            video_url = data['url_overridden_by_dest']
        else:
            raise PWarning("Нет видео в посте")
        return video_url, audio_url

    def get_download_video_and_audio(self, video_url, audio_url):
        do_the_linux_command(f"curl -o {self.tmp_video_file.name} {video_url}")
        do_the_linux_command(f"curl -o {self.tmp_audio_file.name} {audio_url}")

    def mux_video_and_audio(self):
        try:
            do_the_linux_command(
                f"ffmpeg -i {self.tmp_video_file.name} -i {self.tmp_audio_file.name} -c:v copy -c:a aac -strict experimental -f mp4 -y {self.tmp_output_file.name}")
        finally:
            self.delete_video_audio_files()

    def delete_video_audio_files(self):
        self.tmp_video_file.close()
        self.tmp_audio_file.close()

    def delete_output_file(self):
        self.tmp_output_file.close()

    def get_video_bytes(self):
        try:
            with open(self.tmp_output_file.name, 'rb') as file:
                file_bytes = file.read()
        finally:
            self.delete_output_file()
        return file_bytes

    def get_video_from_post(self, post_url) -> bytes:
        """
        Получаем видео с аудио
        """
        parsed_url = urlparse(post_url)
        post_url = f"{parsed_url.scheme}://{parsed_url.hostname}{parsed_url.path}"
        video_url, audio_url = self.get_reddit_video_audio_urls(post_url)
        # Нет нужды делать временные файлы для джоина видео и аудио, если аудио нет, то просто кидаем видео и всё
        if not audio_url:
            return video_url
            # return requests.get(video_url).content
        self.get_download_video_and_audio(video_url, audio_url)
        self.mux_video_and_audio()
        return self.get_video_bytes()
