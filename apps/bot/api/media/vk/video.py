import json
import re
from urllib.parse import urlparse

import requests
import xmltodict
from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait

from apps.bot.api.media.data import VideoData
from apps.bot.api.subscribe_service import SubscribeService, SubscribeServiceNewVideosData, \
    SubscribeServiceNewVideoData, SubscribeServiceData
from apps.bot.classes.const.exceptions import PError
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.utils.utils import extract_json
from apps.bot.utils.video.downloader import VideoDownloader
from apps.bot.utils.video.video_handler import VideoHandler
from apps.bot.utils.web_driver import get_web_driver
from apps.service.models import SubscribeItem


class VKVideo(SubscribeService):
    URL = "https://vkvideo.ru"
    HEADERS = {
        'authority': 'vkvideo.ru',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru-RU,ru;q=0.9',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
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

    # SUBSCRIBE METHODS

    def get_channel_info(self, url: str) -> SubscribeServiceData:
        playlist_id = None
        playlist_title = None

        if 'playlist' in url:
            playlist_info = self._get_playlist_info(url)
            playlist_id = playlist_info['playlist_id']
            playlist_title = playlist_info['playlist_title']
            channel_path = playlist_info['channel_path']
            channel_title = playlist_info['channel_title']
            last_videos_id = playlist_info['last_videos_id']
        else:
            channel_info = self._get_channel_info(url)
            channel_path = channel_info['channel_path']
            channel_title = channel_info['channel_title']
            last_videos_id = channel_info['last_videos_id']
            # last_videos_id = []

        return SubscribeServiceData(
            channel_id=channel_path,
            playlist_id=playlist_id,
            channel_title=channel_title,
            playlist_title=playlist_title,
            last_videos_id=last_videos_id,
            service=SubscribeItem.SERVICE_VK
        )

    def get_filtered_new_videos(
            self,
            channel_id: str,
            last_videos_id: list[str],
            **kwargs
    ) -> SubscribeServiceNewVideosData:
        if playlist_id := kwargs.get('playlist_id'):
            url = self._get_channel_playlist_videos_url(playlist_id)
            videos = self._get_playlist_videos(url)
        else:
            url = self._get_channel_videos_url(channel_id)
            videos = self._get_channel_videos(url)
        ids = videos['ids']
        titles = videos['titles']
        urls = videos['urls']

        index = self.filter_by_id(ids, last_videos_id)
        if len(ids) == index:
            return SubscribeServiceNewVideosData(videos=[])

        ids = ids[index:]
        titles = titles[index:]
        urls = urls[index:]

        data = SubscribeServiceNewVideosData(videos=[])
        for i, _ in enumerate(ids):
            video = SubscribeServiceNewVideoData(
                id=ids[i],
                title=titles[i],
                url=urls[i]
            )
            data.videos.append(video)
        return data

    # -----------------------------

    # UTILS

    @staticmethod
    def _prepare_title(name: str) -> str:
        return name.replace("&#774;", "й")

    def _get_channel_videos_url(self, channel_path: str):
        return f"{self.URL}/{channel_path}"

    def _get_channel_playlist_videos_url(self, playlist_id: str):
        return f"{self.URL}/{playlist_id}"

    def _get_video_url(self, video_id):
        return f"{self.URL}/video{video_id}"

    @staticmethod
    def _get_playlist_path(owner_id, playlist_id):
        return f"playlist/{owner_id}_{playlist_id}"

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

    # CHANNEL/PLAYLISTS INFO GETTERS

    def _get_channel_info(self, url) -> dict:
        data = self._get_channel_data(url)
        videos = data['videos']
        videos = list(reversed(videos))
        last_videos_id = [f"{x['owner_id']}_{x['video_id']}" for x in videos]

        return {
            'channel_path': data['channel_path'],
            'channel_title': data['channel_title'],
            'last_videos_id': last_videos_id
        }

    def _get_channel_videos(self, url):
        data = self._get_channel_data(url)
        videos = data['videos']
        videos = list(reversed(videos))

        ids = [f"{v['owner_id']}_{v['video_id']}" for v in videos]
        return {
            "ids": ids,
            "titles": [self._prepare_title(v['title']) for v in videos],
            "urls": [self._get_video_url(_id) for _id in ids]
        }

    def _get_playlist_info(self, url) -> dict:
        data = self._get_playlist_data(url)
        videos = data['videos']
        videos = list(reversed(videos))
        last_videos_id = [f"{x['owner_id']}_{x['video_id']}" for x in videos]

        return {
            "playlist_id": self._get_playlist_path(data['owner_id'], data['playlist_id']),
            "playlist_title": self._prepare_title(data['playlist_title']),
            "channel_path": data['channel_path'],
            "channel_title": self._prepare_title(data['channel_title']),
            "last_videos_id": last_videos_id,
        }

    def _get_playlist_videos(self, url):
        data = self._get_playlist_data(url)
        videos = data['videos']
        videos = list(reversed(videos))

        ids = [f"{v['owner_id']}_{v['video_id']}" for v in videos]
        return {
            "ids": ids,
            "titles": [self._prepare_title(v['title']) for v in videos],
            "urls": [self._get_video_url(_id) for _id in ids]
        }

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

    def _get_channel_data(self, url):
        web_driver = get_web_driver(headers=self.HEADERS)
        try:
            web_driver.get(url)
            WebDriverWait(web_driver, 10).until(
                lambda x: 'data-testid="video_list_item"' in x.page_source
            )
            page_content = web_driver.page_source
        finally:
            web_driver.quit()

        bs4 = BeautifulSoup(page_content, "html.parser")

        urls_and_titles = [(x.attrs['href'], x.select_one('div[aria-label]').attrs['aria-label']) for x in
                           bs4.select('a[data-testid="video_list_item"]')]

        pattern = re.compile(r'/video(?P<owner_id>-?\d+)_(?P<video_id>\d+)')
        videos = []
        for _url, title in urls_and_titles:
            if match := pattern.search(_url):

                try:
                    slice_index_end = title.index(" длительностью")
                    title = title[:slice_index_end]
                except ValueError:
                    pass

                videos.append({
                    'owner_id': match.group('owner_id'),
                    'video_id': match.group('video_id'),
                    'title': title
                })

        content = requests.get(url, headers=self.HEADERS).content
        bs4 = BeautifulSoup(content, "html.parser")
        channel_data = json.loads(bs4.select_one('.VideoShowcaseCommunityHeader').attrs['data-exec'])[
            'VideoShowcaseCommunityHeader/init']
        return {
            "channel_path": urlparse(url).path.replace('/', ''),
            "channel_title": channel_data['groupName'],
            "owner_id": channel_data['ownerId'],
            "videos": videos,
        }

    def _get_playlist_data(self, url):
        web_driver = get_web_driver(headers=self.HEADERS)
        try:
            web_driver.get(url)
            WebDriverWait(web_driver, 10).until(
                lambda x: 'data-testid="video_card_title"' in x.page_source
            )
            page_content = web_driver.page_source
        finally:
            web_driver.quit()

        bs4 = BeautifulSoup(page_content, "html.parser")

        urls_and_titles = [(x.attrs['href'], x.text) for x in bs4.select('div[data-testid="video_card_title"] a')]

        pattern = re.compile(r'/video(?P<owner_id>-?\d+)_(?P<video_id>\d+)')
        videos = []
        for _url, title in urls_and_titles:
            if match := pattern.search(_url):
                videos.append({
                    'owner_id': match.group('owner_id'),
                    'video_id': match.group('video_id'),
                    'title': title
                })
        owner_id, playlist_id = urlparse(url).path.replace("/playlist/", "").split("_", 1)

        first_breadcrumb = bs4.select('span[data-testid="breadcrumb-label"]')[0]
        last_breadcrumb = bs4.select('span[data-testid="breadcrumb-label"]')[-1]
        return {
            "channel_path": first_breadcrumb.previous.attrs['href'].replace('/', ''),
            "channel_title": first_breadcrumb.text,
            "owner_id": owner_id,
            "videos": videos,
            "playlist_id": playlist_id,
            "playlist_title": last_breadcrumb.text,
        }

    # -----------------------------
