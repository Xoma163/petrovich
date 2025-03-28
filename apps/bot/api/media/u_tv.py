import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from apps.bot.api.media.data import VideoData
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.utils.video.downloader import VideoDownloader


class UTV:
    @staticmethod
    def get_video_info(url: str) -> VideoData:
        content = requests.get(url).content
        bs4 = BeautifulSoup(content, features="lxml")
        src = bs4.select_one(".project__frame").find("iframe").attrs['src']
        parsed_url = urlparse(src)
        new_url = f"{parsed_url[0]}://{parsed_url[1]}{parsed_url[2]}"

        return VideoData(
            title=bs4.select_one(".project__info-title").text,
            channel_id=re.search(r'shows/([^/]+)/episodes', url).group(1),
            channel_title=bs4.select_one(".project__single-name").text,
            m3u8_master_url=f"{new_url}/master.m3u8",
            thumbnail_url=bs4.select_one(f'a.swiper-slide[href="{url}"]').find('img').attrs['src'],
            width=int(bs4.select_one('meta[property="og:image:width"]')['content']),
            height=int(bs4.select_one('meta[property="og:image:height"]')['content'])
        )

    @staticmethod
    def download(data: VideoData) -> VideoAttachment:
        va = VideoAttachment()
        va.m3u8_url = data.m3u8_master_url
        vd = VideoDownloader(va)
        va.content = vd.download_m3u8(threads=10)
        return va