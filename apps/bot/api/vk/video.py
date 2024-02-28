import json
import re
from typing import Tuple, Optional, List
from urllib.parse import urlparse

import requests
import xmltodict
from bs4 import BeautifulSoup

from apps.bot.api.subscribe_service import SubscribeService
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.utils.video.video_handler import VideoHandler


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

    def get_video(self, url) -> bytes:
        player_url = self._get_player_url(url)
        va, aa = self._get_video_audio(player_url)
        if aa is not None:
            vh = VideoHandler(video=va, audio=aa)
            return vh.mux()
        return va.download_content(headers=self.headers)

    def _get_player_url(self, url: str) -> str:
        r = requests.get(url, headers=self.headers)
        bs4 = BeautifulSoup(r.text, 'html.parser')
        og_video = bs4.find("meta", property="og:video")
        if not og_video:
            raise PWarning("К сожалению видео не получится скачать :(")
        player_url = bs4.find("meta", property="og:video").attrs['content']
        return player_url

    def _get_video_audio(self, player_url: str) -> Tuple[VideoAttachment, Optional[AudioAttachment]]:
        r = requests.get(player_url, headers=self.headers)
        js_code = re.findall('var playerParams = (\{.*\})', r.text)[0]
        info = json.loads(js_code)
        info = info.get('params')[0]

        if dash_webm := info.get('dash_webm'):
            return self._get_video_audio_dash(dash_webm)
        elif dash_sep := info.get('dash_sep'):
            return self._get_video_audio_dash(dash_sep)
        elif hls := info.get('hls'):
            return self._get_video_hls(hls)

    def _get_video_audio_dash(self, dash_webm_url) -> Tuple[VideoAttachment, AudioAttachment]:
        parsed_url = urlparse(dash_webm_url)

        r = requests.get(dash_webm_url, headers=self.headers).content
        dash_webm_dict = xmltodict.parse(r)
        adaptation_sets = dash_webm_dict['MPD']['Period']['AdaptationSet']

        video_representations = adaptation_sets[0]['Representation']
        video_representations = list(sorted(video_representations, key=lambda x: int(x['@bandwidth'])))

        audio_representations = adaptation_sets[1]['Representation']
        audio_representations = list(sorted(audio_representations, key=lambda x: int(x['@bandwidth'])))

        aa = AudioAttachment()
        aa.public_download_url = f"{parsed_url.scheme}://{parsed_url.hostname}/{audio_representations[-1]['BaseURL']}"
        aa.download_content(headers=self.headers, stream=True)
        va = VideoAttachment()
        va.public_download_url = f"{parsed_url.scheme}://{parsed_url.hostname}/{video_representations[-1]['BaseURL']}"
        va.download_content(headers=self.headers, stream=True)

        return va, aa

    @staticmethod
    def _get_video_hls(hls_url) -> Tuple[VideoAttachment, None]:
        va = VideoAttachment()
        va.m3u8_url = hls_url
        return va, None

    def get_video_info(self, url) -> dict:
        content = requests.get(url, headers=self.headers).content
        bs4 = BeautifulSoup(content, 'html.parser')
        try:

            og_title = bs4.find('meta', property="og:title")
            video_title = ""
            if og_title:
                video_title = og_title.attrs['content']

            if "clip-" in url:
                video_id = urlparse(url).path.split('clip')[1]
                try:
                    a_tag = bs4.select_one('.ui_crumb')
                    channel_id = f"@{a_tag.attrs['href'].split('/')[-1]}"
                    channel_title = a_tag.te
                except:
                    channel_id = bs4.select_one('title').text.split(" | ")[0].lstrip("Клипы ")
                    channel_title = channel_id
            else:
                a_tag = bs4.select_one(".VideoCard__additionalInfo a")

                video_id = urlparse(url).path.split('video')[1]
                channel_id = a_tag.attrs['href'].split('/')[-1]
                channel_title = a_tag.text

            return {
                'channel_id': channel_id,
                'video_id': video_id,
                'channel_title': channel_title,
                'video_title': video_title
            }
        except Exception:
            return {}

    def get_data_to_add_new_subscribe(self, url: str) -> dict:
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

            channel_id = video_info['channel_id']
            channel_title = video_info['channel_title']
        else:
            channel_id = bs4.select_one('.VideoCard__additionalInfo a').attrs['href'].split('/')[-1]
            channel_title = bs4.select_one(".VideoCard__ownerLink").text
            videos = bs4.find('div', {'id': "video_subtab_pane_all"}).find_all('div', {'class': 'VideoCard__info'})
            playlist_id = None
            playlist_title = None
            last_videos_id = list(
                reversed([x.find("a", {"class": "VideoCard__title"}).attrs['data-id'] for x in videos]))

        return {
            'channel_id': channel_id,
            'playlist_id': playlist_id,
            'channel_title': channel_title,
            'playlist_title': playlist_title,
            'last_videos_id': last_videos_id,
        }

    def get_filtered_new_videos(self, channel_id: str, last_videos_id: List[str], **kwargs) -> dict:
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
        urls = [f"{self.URL}{x}" for x in ids]
        return {"ids": ids, "titles": titles, "urls": urls}

    @staticmethod
    def _get_playlist_data(bs4):
        bs4_str = str(bs4)
        pos1_text = "extend(window.cur || {}, "
        pos2_text = ");Promise"
        pos1 = bs4_str.find(pos1_text)
        pos2 = bs4_str.find(pos2_text, pos1)
        data = json.loads(bs4_str[pos1 + len(pos1_text):pos2])
        return data
