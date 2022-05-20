import requests


class WASDAPI:
    URL = "https://wasd.tv/"

    def __init__(self):
        self.channel_id = None
        self.title = None

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
