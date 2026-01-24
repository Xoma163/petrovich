import json
import re
from urllib.parse import urlparse

import requests
import xmltodict
from bs4 import BeautifulSoup

from apps.bot.core.messages.attachments.audio import AudioAttachment
from apps.bot.core.messages.attachments.video import VideoAttachment
from apps.bot.utils.utils import extract_json
from apps.bot.utils.video.downloader import VideoDownloader
from apps.bot.utils.video.video_handler import VideoHandler
from apps.connectors.parsers.media_command.data import VideoData
from apps.shared.exceptions import PError


class VKVideo:
    URL = "https://vkvideo.ru"
    HEADERS = {
        'authority': 'vkvideo.ru',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru-RU,ru;q=0.9',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24""',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    }

    def __init__(self):
        super().__init__()

    # SERVICE METHODS

    def get_video_info(self, url) -> VideoData:
        content = requests.get(url, headers=self.HEADERS).content
        bs4 = BeautifulSoup(content, 'html.parser')
        try:

            og_title = bs4.find('meta', property="og:title")
            video_title = ""
            if og_title:
                video_title = og_title.attrs['content']

            if "clip-" in url:
                video_id = urlparse(url).path.split('clip')[1]
                channel_id = video_id.split('_', 1)[0]
                try:
                    a_tag = bs4.select_one('.ui_crumb')
                    channel_title = a_tag.te
                except:
                    channel_title = channel_id
            else:
                short_video_data = self._get_short_video_data(bs4)
                video_data = self._get_video_data(bs4)
                video_id = short_video_data['videoId']
                channel_id = short_video_data['ownerId']
                channel_title = video_data['playlistAddedTitle'].split(' ', 1)[1]

            try:
                width = bs4.find('meta', {'property': 'og:video:width'})['content']
                height = bs4.find('meta', {'property': 'og:video:height'})['content']
            except (AttributeError, KeyError, TypeError):
                width = None
                height = None

            # Лишний текст
            channel_title = channel_title.replace("Видеозаписи ", "")
            return VideoData(
                channel_id=channel_id,
                video_id=video_id,
                channel_title=channel_title,
                title=video_title,
                width=width,
                height=height
            )
        except Exception as e:
            raise PError("Не смог получить информацию о видео") from e

    def download_video(self, url: str, author_id: int, video_id: str, high_res: bool = False) -> VideoAttachment:
        player_url = self._get_player_url(url, author_id, video_id)

        va, aa = self._get_video_audio(player_url, high_res=high_res)

        if aa is not None:
            va.download_content(stream=True)
            aa.download_content(stream=True)
            vh = VideoHandler(video=va, audio=aa)
            va.content = vh.mux()
        if va.m3u8_url:
            vd = VideoDownloader(va)
            va.content = vd.download_m3u8(threads=10)  # ToDo: тут не передаются хедеры, возможно будет проблема

        # va.download_content(headers=self.HEADERS)
        return va

    # -----------------------------

    # VIDEO DOWNLOAD HELPERS

    def _get_player_url(self, url: str, author_id: int, video_id: str) -> str:
        r = requests.get(url, headers=self.HEADERS)
        bs4 = BeautifulSoup(r.text, 'html.parser')
        if og_video := bs4.find("meta", property="og:video"):
            player_url = og_video.attrs['content']
        elif "clip-" in url:
            player_url = f"{self.URL}/video_ext.php?oid={author_id}&id={video_id.split('_')[1]}"
        else:
            player_url = f"{self.URL}/video_ext.php?oid={author_id}&id={video_id}"
        return player_url

    def _get_video_audio(self, player_url: str, high_res: bool) -> tuple[VideoAttachment, AudioAttachment | None]:
        r = requests.get(player_url, headers=self.HEADERS)
        js_code = re.findall(r';window.cur = Object.assign\(window.cur |\| \{\}, ({.*?})\)', r.text)[-1]
        info = json.loads(extract_json(js_code))
        info = info['apiPrefetchCache'][0]['response']['items'][0]

        # Если не будет работать, то можно попробовать через поля 'url2160/url1440/url1080/url720/url480/url360/url240'
        va = None
        aa = None

        files = info.get('files', {})

        dash = files.get('dash_sep')
        hls = files.get('hls') or info.get('hls_ondemand')
        # Iphone не умеют в WEBM
        dash_webm = files.get('dash_webm')

        if dash:
            va, aa = self._get_video_audio_dash(dash, high_res=high_res)
        elif hls:
            va, aa = self._get_video_hls(hls)
        elif dash_webm:
            va, aa = self._get_video_audio_dash(dash_webm, high_res=high_res)
        if va:
            va.thumbnail_url = info.get('short_video_cover', info.get('jpg'))
        return va, aa

    def _get_video_audio_dash(self, dash_webm_url: str, high_res: bool) -> tuple[VideoAttachment, AudioAttachment]:
        parsed_url = urlparse(dash_webm_url)

        r = requests.get(dash_webm_url, headers=self.HEADERS).content
        dash_webm_dict = xmltodict.parse(r)
        adaptation_sets = dash_webm_dict['MPD']['Period']['AdaptationSet']

        if isinstance(adaptation_sets, dict):
            video_representations = adaptation_sets['Representation']
            video_representations = list(
                sorted(video_representations, key=lambda x: int(x['@bandwidth']), reverse=True)
            )
            aa = None
        else:
            video_representations = adaptation_sets[0]['Representation']
            video_representations = list(
                sorted(video_representations, key=lambda x: int(x['@bandwidth']), reverse=True)
            )

            audio_representations = adaptation_sets[1]['Representation']
            audio_representations = list(
                sorted(audio_representations, key=lambda x: int(x['@bandwidth']), reverse=True)
            )

            aa = AudioAttachment()
            aa.public_download_url = f"{parsed_url.scheme}://{parsed_url.hostname}/{audio_representations[0]['BaseURL']}"
            aa.download_content(headers=self.HEADERS, stream=True)

        vr = video_representations[0]
        if not high_res:
            for vr in video_representations:
                if int(vr['@height']) <= 1080:
                    break

        va = VideoAttachment()
        va.public_download_url = f"{parsed_url.scheme}://{parsed_url.hostname}/{vr['BaseURL']}"
        va.download_content(headers=self.HEADERS, stream=True)

        return va, aa

    @staticmethod
    def _get_video_hls(hls_url) -> tuple[VideoAttachment, None]:
        va = VideoAttachment()
        va.m3u8_url = hls_url
        return va, None

    # -----------------------------

    # DATA GETTERS

    @staticmethod
    def _get_short_video_data(bs4):
        bs4_str = str(bs4)
        pos1_text = "initReactApplication('Video_page', "
        pos2_text = ");"
        pos1 = bs4_str.find(pos1_text)
        pos2 = bs4_str.find(pos2_text, pos1)
        data = json.loads(bs4_str[pos1 + len(pos1_text):pos2])
        return data

    @staticmethod
    def _get_video_data(bs4) -> dict:
        bs4_str = str(bs4)
        pos1_text = "var newCur = "
        pos2_text = "};"
        pos1 = bs4_str.find(pos1_text) - 1
        pos2 = bs4_str.find(pos2_text, pos1) + 1
        data = json.loads(bs4_str[pos1 + len(pos1_text):pos2])
        del data['lang']
        return data
