import requests


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
        m3u8_file = channel_media_data['media_container_streams'][0]['stream_media'][0]['media_meta'][
            'media_archive_url']

        master_m3u8 = requests.get(m3u8_file).text
        master_m3u8_lines = master_m3u8.split('\n')
        # ToDo: max quality
        for i, line in enumerate(master_m3u8_lines):
            if "1920x1080" in line:
                m3u8_1080p = master_m3u8_lines[i + 1]
                break
        prepend_text = f"{self.CDN_URL}live/{user_id}"
        m3u8_url = f"{prepend_text}/{m3u8_1080p}"
        m3u8 = requests.get(m3u8_url).text
        m3u8_list = m3u8.split("\n")
        new_m3u8 = []
        next_line_replace = False
        for row in m3u8_list:
            if row.startswith("#EXTINF:"):
                next_line_replace = True
            elif next_line_replace:
                next_line_replace = False
                row = f"{prepend_text}/{row}"
            new_m3u8.append(row)
        self.m3u8_str = str.encode("\n".join(new_m3u8))
