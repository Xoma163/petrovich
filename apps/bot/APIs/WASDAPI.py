import requests

from apps.bot.utils.utils import get_max_quality_m3u8_url, prepend_url_to_m3u8


class WASDAPI:
    URL = "https://wasd.tv/"
    CDN_URL = "https://cdn-volta.wasd.tv/"

    def __init__(self):
        self.channel_id = None
        self.title = None
        self.show_name = None
        self.m3u8_str = None

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
        self.title = channel_media_data['media_container_name']
        self.show_name = channel_media_data['media_container_user']['user_login']
        master_m3u8_url = channel_media_data['media_container_streams'][0]['stream_media'][0]['media_meta'][
            'media_archive_url']
        master_m3u8 = requests.get(master_m3u8_url).text
        m3u8_max_quality_url = get_max_quality_m3u8_url(master_m3u8)
        prepend_text = f"{self.CDN_URL}live/{user_id}"
        m3u8_url = f"{prepend_text}/{m3u8_max_quality_url}"
        m3u8 = requests.get(m3u8_url).text
        m3u8 = prepend_url_to_m3u8(m3u8, prepend_text)
        self.m3u8_str = str.encode("\n".join(m3u8))
