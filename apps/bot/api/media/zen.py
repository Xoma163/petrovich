import dataclasses
import json
import re

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from apps.bot.api.media.data import VideoData
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.utils.video.video_handler import VideoHandler


@dataclasses.dataclass
class ZenVideoData:
    channel_id: str
    channel_title: str
    playlist_id: str
    playlist_title: str
    video_id: str
    video_title: str
    m3u8_master_url: str
    thumbnail_url: str


class Zen:
    @staticmethod
    def parse_video(url: str) -> VideoData:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)

        driver.get(url)
        bs4 = BeautifulSoup(driver.page_source, "html.parser")
        driver.close()

        scripts = [x.text for x in bs4.find_all('script') if "master.m3u8" in x.text]
        script = scripts[0]

        re_str = r"\!function\(\)\{\"use strict\";\!function\(a\)\{var e\=window,n\=a\.namespaceKey\?e\[a\.namespaceKey\]\|\|\(e\[a\.namespaceKey\]\=\{\}\)\:e;for\(var t in a\.data\)a\.data\.hasOwnProperty\(t\)&&\(n\[t\]\=a\.data\[t\]\)\}\(\((.*)\)\)}\(\);"
        res = re.findall(re_str, script)
        data = json.loads(res[0])

        video_data = data['data']['MICRO_APP_SSR_DATA']['settings']['exportData']['video']
        m3u8_master_url = [x for x in video_data['video']['streams'] if "master.m3u8" in x][0]

        try:
            resolution = video_data['video']['resolutions'][-1]
            width = resolution['width']
            height = resolution['height']
        except (KeyError, IndexError):
            width = None
            height = None

        return VideoData(
            channel_id=video_data['publisherId'],
            channel_title=video_data['source']['title'],
            # ToDo: пригодится для подписок
            # playlist_id=video_data['collectionMetaAndItem']['meta']['id'],
            # playlist_title=video_data['collectionMetaAndItem']['meta']['title'],
            video_id=video_data['id'],
            title=video_data['title'],
            thumbnail_url=video_data['image'],
            m3u8_master_url=m3u8_master_url,
            width=width,
            height=height
        )

    @staticmethod
    def download_video(m3u8_master_url) -> VideoAttachment:
        va = VideoAttachment()
        va.m3u8_url = m3u8_master_url
        vh = VideoHandler(video=va)
        va.content = vh.download()
        return va
