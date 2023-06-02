import requests
from bs4 import BeautifulSoup

from apps.bot.utils.M3U8 import M3U8


class TheHoleAPI:
    URL = "https://the-hole.tv"
    CDN_URL = "https://video-cdn.the-hole.tv"

    def __init__(self):
        self.channel_id = None
        self.title = None
        self.last_video_id = None
        self.show_name = None
        self.m3u8_bytes = None

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
        base_uri = f"{self.CDN_URL}/episodes/{_id}"

        master_m3u8_url = f"{base_uri}/master.m3u8"
        master_m3u8 = requests.get(master_m3u8_url).text
        _m3u8 = M3U8(master_m3u8, base_uri=base_uri, load_playlists=False, load_high_quality_playlist=True)
        m3u8 = _m3u8.get_playlist_with_best_quality().loaded.dumps_bytes()
        self.m3u8_bytes = m3u8

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
