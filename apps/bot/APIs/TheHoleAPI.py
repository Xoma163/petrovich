import requests
from bs4 import BeautifulSoup

from apps.bot.APIs.SubscribeService import SubscribeService
from apps.bot.utils.VideoDownloader import VideoDownloader


class TheHoleAPI(SubscribeService):
    URL = "https://the-hole.tv"
    CDN_URL = "https://video-cdn.the-hole.tv"

    def __init__(self):
        super().__init__()
        self.channel_id = None
        self.channel_title = None
        self.video_id = None
        self.video_title = None
        self.m3u8_url = None

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

    def get_video(self, url):
        if not self.m3u8_url:
            self.parse_video(url)

        vd = VideoDownloader()
        return vd.download(self.m3u8_url)

    def get_data_to_add_new_subscribe(self, url) -> dict:
        content = requests.get(url).content
        bs4 = BeautifulSoup(content, 'html.parser')
        return {
            'channel_id': url.split('/')[-1],
            'title': bs4.find('meta', attrs={'name': 'og:title'}).attrs['content'],
            'last_video_id': bs4.select_one('a[href*=episodes]').attrs['href'],
            'playlist_id': None
        }

    def get_filtered_new_videos(self, channel_id, last_video_id, **kwargs) -> dict:
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
        urls = [f"{self.URL}{link}" for link in last_videos]

        return {"ids": last_videos, "titles": titles, "urls": urls}
