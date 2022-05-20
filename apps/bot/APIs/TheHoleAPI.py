import requests
from bs4 import BeautifulSoup

from apps.bot.utils.utils import get_max_quality_m3u8_url, prepend_url_to_m3u8


class TheHoleAPI:
    URL = "https://the-hole.tv/"
    CDN_URL = "https://video-cdn.the-hole.tv/"

    def __init__(self):
        self.channel_id = None
        self.title = None
        self.last_video_id = None
        self.show_name = None
        self.m3u8_str = None

    def parse_channel(self, url):
        content = requests.get(url).content
        bs4 = BeautifulSoup(content, 'html.parser')
        self.title = bs4.find('meta', attrs={'name': 'og:title'}).attrs['content']
        self.channel_id = url.split('/')[-1]
        self.last_video_id = bs4.select_one('a[href*=episodes]').attrs['href']

    def parse_video(self, url):
        content = requests.get(url).content
        bs4 = BeautifulSoup(content, 'html.parser')
        self.show_name = \
            [x.text for x in bs4.select('a[href*=shows]') if x.attrs['href'].startswith("/shows/") if x.text.strip()][0]

        data_player = bs4.select_one('[data-player-source-value]').attrs
        master_m3u8 = data_player['data-player-source-value']
        self.title = data_player['data-player-title-value']
        # title = bs4.find('meta', attrs={'name': "og:title"}).attrs['content']

        _id = master_m3u8.split("/")[-2]
        prepend_text = f"{self.CDN_URL}episodes/{_id}"

        master_m3u8_url = f"{prepend_text}/master.m3u8"
        master_m3u8 = requests.get(master_m3u8_url).text
        m3u8_max_quality_url = get_max_quality_m3u8_url(master_m3u8)
        m3u8_url = f"{prepend_text}/{m3u8_max_quality_url}"
        m3u8 = requests.get(m3u8_url).text
        m3u8 = prepend_url_to_m3u8(m3u8, prepend_text)
        self.m3u8_str = str.encode("\n".join(m3u8))

    def get_last_videos_with_titles(self, channel_id):
        content = requests.get(f"{self.URL}shows/{channel_id}").content
        bs4 = BeautifulSoup(content, 'html.parser')
        last_videos = [x.attrs['href'] for x in bs4.select('a[href*=episodes]')]
        titles = [x.nextSibling.nextSibling.text for x in bs4.select('a[href*=episodes]')]
        return last_videos, titles
