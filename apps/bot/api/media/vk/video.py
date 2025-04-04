import json
import json
import re
from urllib.parse import urlparse

import requests
import xmltodict
from bs4 import BeautifulSoup

from apps.bot.api.media.data import VideoData
from apps.bot.api.subscribe_service import SubscribeService, SubscribeServiceNewVideosData, \
    SubscribeServiceNewVideoData, SubscribeServiceData
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.utils.video.downloader import VideoDownloader
from apps.bot.utils.video.video_handler import VideoHandler
from apps.service.models import SubscribeItem


class VKVideo(SubscribeService):
    URL = "https://vk.com/video"
    headers = {
        'authority': 'vk.com',
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

    def download(self, url: str, video_id: str, high_res: bool = False) -> VideoAttachment:
        player_url = self._get_player_url(url, video_id)
        va, aa = self._get_video_audio(player_url, high_res=high_res)

        if aa is not None:
            va.download_content(stream=True)
            aa.download_content(stream=True)
            vh = VideoHandler(video=va, audio=aa)
            va.content = vh.mux()
        if va.m3u8_url:
            vd = VideoDownloader(va)
            va.content = vd.download_m3u8(threads=10)  # ToDo: тут не передаются хедеры, возможно будет проблема

        # va.download_content(headers=self.headers)
        return va

    def _get_player_url(self, url: str, video_id: str) -> str:
        r = requests.get(url, headers=self.headers)
        bs4 = BeautifulSoup(r.text, 'html.parser')
        og_video = bs4.find("meta", property="og:video")
        if og_video:
            player_url = bs4.find("meta", property="og:video").attrs['content']
        else:
            author_id, video_id = video_id.split('_')
            player_url = f"https://vk.com/video_ext.php?oid={author_id}&id={video_id}"
        return player_url

    def _get_video_audio(self, player_url: str, high_res: bool) -> tuple[VideoAttachment, AudioAttachment | None]:
        r = requests.get(player_url, headers=self.headers)
        js_code = re.findall(r'var playerParams = (\{.*\})', r.text)[0]
        info = json.loads(js_code)
        info = info.get('params')[0]

        # Если не будет работать, то можно попробовать через поля 'url2160/url1440/url1080/url720/url480/url360/url240'
        va = None
        aa = None

        dash = info.get('dash_sep')
        hls = info.get('hls', info.get('hls_ondemand'))
        # Iphone не умеют в WEBM
        dash_webm = info.get('dash_webm')

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

        r = requests.get(dash_webm_url, headers=self.headers).content
        dash_webm_dict = xmltodict.parse(r)
        adaptation_sets = dash_webm_dict['MPD']['Period']['AdaptationSet']

        if isinstance(adaptation_sets, dict):
            video_representations = adaptation_sets['Representation']
            video_representations = list(
                sorted(video_representations, key=lambda x: int(x['@bandwidth']), reverse=True))
            aa = None
        else:
            video_representations = adaptation_sets[0]['Representation']
            video_representations = list(
                sorted(video_representations, key=lambda x: int(x['@bandwidth']), reverse=True))

            audio_representations = adaptation_sets[1]['Representation']
            audio_representations = list(
                sorted(audio_representations, key=lambda x: int(x['@bandwidth']), reverse=True))

            aa = AudioAttachment()
            aa.public_download_url = f"{parsed_url.scheme}://{parsed_url.hostname}/{audio_representations[0]['BaseURL']}"
            aa.download_content(headers=self.headers, stream=True)

        vr = video_representations[0]
        if not high_res:
            for vr in video_representations:
                if int(vr['@height']) <= 1080:
                    break

        va = VideoAttachment()
        va.public_download_url = f"{parsed_url.scheme}://{parsed_url.hostname}/{vr['BaseURL']}"
        va.download_content(headers=self.headers, stream=True)

        return va, aa

    @staticmethod
    def _get_video_hls(hls_url) -> tuple[VideoAttachment, None]:
        va = VideoAttachment()
        va.m3u8_url = hls_url
        return va, None

    def get_video_info(self, url) -> VideoData:
        content = requests.get(url, headers=self.headers).content
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
                channel_title=self._prepare_title(channel_title),
                title=self._prepare_title(video_title),
                width=width,
                height=height
            )
        except Exception as e:
            raise PWarning("Не смог получить информацию о видео") from e

    def get_channel_info(self, url: str) -> SubscribeServiceData:
        content = requests.get(url, headers=self.headers).content
        bs4 = BeautifulSoup(content, "html.parser")
        if 'playlist' in url:
            data = self._get_playlist_data(bs4)
            _playlist_id = url.rsplit('_', 1)[1]
            owner_id = data['apiPrefetchCache'][1]['response']['owner_id']
            playlist_id = f"playlist/{owner_id}_{_playlist_id}"
            playlist_title = data['apiPrefetchCache'][1]['response']['title']

            videos = data['apiPrefetchCache'][0]['response']['items']
            videos = list(reversed(videos))
            last_videos_id = [f"{x['owner_id']}_{x['id']}" for x in videos]

            video_info = self.get_video_info(f"https://vk.com/video{last_videos_id[-1]}")

            channel_id = video_info.channel_id
            channel_title = video_info.channel_title
        else:
            channel_id = bs4.select_one('.VideoCard__additionalInfo a').attrs['href'].split('/')[-1]
            channel_title = bs4.select_one(".VideoCard__ownerLink").text
            videos = bs4.find('div', {'id': "video_subtab_pane_all"}).find_all('div', {'class': 'VideoCard__info'})
            playlist_id = None
            playlist_title = None
            last_videos_id = list(
                reversed([x.find("a", {"class": "VideoCard__title"}).attrs['data-id'] for x in videos])
            )

        return SubscribeServiceData(
            channel_id=channel_id,
            playlist_id=playlist_id,
            channel_title=self._prepare_title(channel_title),
            playlist_title=self._prepare_title(playlist_title),
            last_videos_id=last_videos_id,
            service=SubscribeItem.SERVICE_VK
        )

    def get_filtered_new_videos(
            self,
            channel_id: str,
            last_videos_id: list[str],
            **kwargs
    ) -> SubscribeServiceNewVideosData:

        if kwargs.get('playlist_id'):
            channel_id = kwargs['playlist_id']
        url = f"{self.URL}/{channel_id}"
        content = requests.get(url, headers=self.headers).content
        bs4 = BeautifulSoup(content, "html.parser")

        if 'playlist' in url:
            data = self._get_playlist_data(bs4)
            videos = data['apiPrefetchCache'][0]['response']['items']
            videos = list(reversed(videos))

            ids = [f"{x['owner_id']}_{x['id']}" for x in videos]
            titles = [x['title'] for x in videos]
        else:
            videos = bs4.find('div', {'id': "video_subtab_pane_all"}).find_all('div', {'class': 'VideoCard__info'})
            videos = list(reversed(videos))
            ids = [video.find('a', {'class': 'VideoCard__title'}).attrs['data-id'] for video in videos]
            titles = [video.find('a', {'class': 'VideoCard__title'}).text.strip() for video in videos]

        index = self.filter_by_id(ids, last_videos_id)

        ids = ids[index:]
        titles = titles[index:]

        titles = [self._prepare_title(x) for x in titles]

        data = SubscribeServiceNewVideosData(videos=[])
        for i, _id in enumerate(ids):
            data.videos.append(
                SubscribeServiceNewVideoData(
                    id=ids[i],
                    title=titles[i],
                    url=f"{self.URL}{_id}"
                )
            )
        return data

    @staticmethod
    def _prepare_title(name: str) -> str:
        return name.replace("&#774;", "й")

    @staticmethod
    def _get_short_video_data(bs4):
        bs4_str = str(bs4)
        pos1_text = "window.initReactApplication('Video_page', "
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

    @staticmethod
    def _get_playlist_data(bs4):
        bs4_str = str(bs4)
        pos1_text = '{"apiPrefetchCache"'
        pos2_text = ");Promise"
        pos1 = bs4_str.find(pos1_text)
        pos2 = bs4_str.find(pos2_text, pos1)
        data = json.loads(pos1_text + bs4_str[pos1 + len(pos1_text):pos2])
        return data
