import os
from tempfile import NamedTemporaryFile

import requests
from bs4 import BeautifulSoup

from apps.bot.utils.DoTheLinuxComand import do_the_linux_command


class TheHoleAPI:
    URL = "https://the-hole.tv"
    CDN_URL = "https://video-cdn.the-hole.tv"

    def __init__(self):
        self.channel_id = None
        self.channel_title = None
        self.video_id = None
        self.video_title = None
        self.m3u8_url = None

    @staticmethod
    def parse_channel(url):
        content = requests.get(url).content
        bs4 = BeautifulSoup(content, 'html.parser')
        return {
            'title': bs4.find('meta', attrs={'name': 'og:title'}).attrs['content'],
            'channel_id': url.split('/')[-1],
            'last_video_id': bs4.select_one('a[href*=episodes]').attrs['href']
        }

    def parse_video(self, url):
        content = requests.get(url).content
        bs4 = BeautifulSoup(content, 'html.parser')

        a = [x for x in bs4.select('a[href*=shows]') if x.attrs['href'].startswith("/shows/") if x.text.strip()][0]
        self.channel_id = a.attrs['href'].replace("/shows/", "")

        data_player = bs4.select_one('[data-player-source-value]').attrs
        self.channel_title = a.text
        self.video_title = data_player['data-player-title-value']
        master_m3u8 = data_player['data-player-source-value']
        self.video_id = master_m3u8.split("/")[-2]
        base_uri = f"{self.CDN_URL}/episodes/{self.video_id}"

        self.m3u8_url = f"{base_uri}/master.m3u8"

    def get_last_videos_with_titles(self, channel_id, last_video_id=None):
        content = requests.get(f"{self.URL}/shows/{channel_id}").content
        bs4 = BeautifulSoup(content, 'html.parser')
        last_videos = [x.attrs['href'] for x in bs4.select('a[href*=episodes]')]
        titles = [x.nextSibling.nextSibling.text for x in bs4.select('a[href*=episodes]')]

        if last_video_id:
            try:
                index = last_videos.index(last_video_id)
                last_videos = last_videos[:index]
                titles = titles[:index]
            except IndexError:
                pass

        last_videos = list(reversed(last_videos))
        titles = list(reversed(titles))

        return last_videos, titles

    def get_video(self, url):
        if not self.m3u8_url:
            self.parse_video(url)

        tmp_video_file = NamedTemporaryFile().name
        try:
            do_the_linux_command(f"yt-dlp -o {tmp_video_file} {self.m3u8_url}")
            with open(tmp_video_file, 'rb') as file:
                video_content = file.read()
        finally:
            os.remove(tmp_video_file)
        return video_content
