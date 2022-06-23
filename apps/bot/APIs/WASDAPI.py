import requests

from apps.bot.utils.M3U8 import M3U8


class WASDAPI:
    URL = "https://wasd.tv/"
    CDN_URL = "https://cdn-volta.wasd.tv/"

    def __init__(self):
        self.channel_id = None
        self.title = None
        self.show_name = None
        self.m3u8_bytes = None

    def get_m3u8(self):
        pass

    def parse_channel(self, url):
        last_part = url.split('/')[-1]

        try:
            self.channel_id = int(last_part)
            self.title = requests.get(f"{self.URL}api/v2/channels/{self.channel_id}").json()['result']['channel_name']
        except ValueError:
            self.title = last_part
            self.channel_id = requests.get(
                f"{self.URL}api/v2/broadcasts/public",
                params={"with_extra": "true", "channel_name": self.title}).json()['result']['channel']['channel_id']

    def parse_video_m3u8(self, url):
        if not self.channel_id:
            self.parse_channel(url)
        channel_media_data = \
            requests.get(f"{self.URL}api/v2/media-containers", params={"channel_id": self.channel_id}).json()['result'][
                0]
        user_id = channel_media_data['user_id']
        base_uri = f"{self.CDN_URL}live/{user_id}"

        self.title = channel_media_data['media_container_name']
        self.show_name = channel_media_data['media_container_user']['user_login']
        master_m3u8_url = channel_media_data['media_container_streams'][0]['stream_media'][0] \
            ['media_meta']['media_archive_url']

        master_m3u8 = requests.get(master_m3u8_url).text
        base_playlist_uri = f"https://cdn-volta.wasd.tv/live/{user_id}/"
        _m3u8 = M3U8(master_m3u8, base_uri=base_uri, load_playlists=False, load_high_quality_playlist=True,
                     base_playlists_uri=base_playlist_uri)
        m3u8 = _m3u8.get_playlist_with_best_quality().loaded.dumps_bytes()
        self.m3u8_bytes = m3u8

    def channel_is_live(self, title):
        r = requests.get(f"{self.URL}api/v2/broadcasts/public",
                         params={"with_extra": "true", "channel_name": title}, timeout=5).json()
        self.title = r['result']['media_container']['media_container_name']

        return r['result']['channel']['channel_is_live']
