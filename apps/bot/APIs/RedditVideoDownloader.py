import datetime
import os
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from apps.bot.classes.Exceptions import PWarning


class RedditVideoSaver:
    def __init__(self):
        self.timestamp = datetime.datetime.now().timestamp()
        self.video_filename = f"/tmp/video_{self.timestamp}.mp4"
        self.audio_filename = None # Уточняется в процессе
        self.output_filename = f"/tmp/output_{self.timestamp}.mp4"

    def check_valid_url(self, post_url):
        hostname = urlparse(post_url).hostname
        if hostname in ["www.reddit.com"]:
            return True
        raise PWarning("Невалидная ссылка на редит")

    def set_audio_filename(self, filename):
        audio_format = filename.split('.')[-1]
        self.audio_filename = f"audio_{self.timestamp}.{audio_format}"

    def parse_mpd_audio_filename(self, url):
        """
        Достаём имя файла на сервере реддита. Если его нет, то по умолчанию это "audio"
        Если нашли имя файла, то также проставляем формат файла
        """
        xml = requests.get(url).content
        bs4 = BeautifulSoup(xml, 'html.parser')
        try:
            filename = bs4.find("adaptationset", {'contenttype': 'audio'}).find('representation').find('baseurl').text
            self.set_audio_filename(filename)
            return filename
        except:
            try:
                filename = bs4.find("representation", {'id': 'AUDIO-1'}).find('baseurl').text
                self.set_audio_filename(filename)
                return filename
            except:
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
        media_data = data["media"]
        if not media_data:
            data = data['crosspost_parent_list'][0]
            media_data = data["media"]

        video_url = media_data["reddit_video"]["fallback_url"]
        audio_filename = self.parse_mpd_audio_filename(media_data['reddit_video']['dash_url'])

        audio_url = None
        if audio_filename:
            audio_url = video_url.split("DASH_")[0] + audio_filename

        return video_url, audio_url

    def get_download_video_and_audio(self, video_url, audio_url):
        os.system(f"curl -o {self.video_filename} {video_url}")
        if audio_url:
            os.system(f"curl -o {self.audio_filename} {audio_url}")

    def mux_video_and_audio(self):
        try:
            if self.audio_filename:
                os.system(f"ffmpeg -i {self.video_filename} -i {self.audio_filename} -c:v copy -c:a aac -strict experimental {self.output_filename}")
            else:
                os.system(f"ffmpeg -i {self.video_filename} -c:v copy -c:a aac -strict experimental {self.output_filename}")
        finally:
            self.delete_video_audio_files()

    def delete_video_audio_files(self):
        os.system(f"rm {self.video_filename}")
        os.system(f"rm {self.audio_filename}")

    def delete_output_file(self):
        os.system(f"rm {self.output_filename}")

    def get_video_bytes(self):
        try:
            with open(self.output_filename, 'rb') as file:
                file_bytes = file.read()
        finally:
            self.delete_output_file()
        return file_bytes

    def get_video_from_post(self, post_url) -> bytes:
        """
        Получаем видео с аудио
        """
        self.check_valid_url(post_url)
        video_url, audio_url = self.get_reddit_video_audio_urls(post_url)
        self.get_download_video_and_audio(video_url, audio_url)
        self.mux_video_and_audio()
        return self.get_video_bytes()

    def has_video(self):
        pass
