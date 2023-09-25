import requests
from bs4 import BeautifulSoup

from apps.bot.api.subscribe_service import SubscribeService
from apps.bot.utils.video.downloader import VideoDownloader


class TheHole(SubscribeService):
    URL = "https://the-hole.tv"
    CDN_URL = "https://video-cdn.the-hole.tv"

    def parse_video(self, url):
        content = requests.get(url).content
        bs4 = BeautifulSoup(content, 'html.parser')

        a = [x for x in bs4.select('a[href*=shows]') if x.attrs['href'].startswith("/shows/") if x.text.strip()][0]

        data_player = bs4.select_one('[data-player-source-value]').attrs
        master_m3u8 = data_player['data-player-source-value']
        video_id = master_m3u8.split("/")[-1]
        base_uri = f"{self.CDN_URL}/episodes/{video_id}"

        return {
            "channel_id": a.attrs['href'].replace("/shows/", ""),
            "channel_title": a.text,
            "video_id": video_id,
            "video_title": data_player['data-player-title-value'],
            "m3u8_url": f"{base_uri}/master.m3u8",
        }

    @staticmethod
    def download_video(m3u8_url: str) -> bytes:
        vd = VideoDownloader()
        return vd.download(m3u8_url)

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
