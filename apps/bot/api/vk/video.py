import json
from typing import Tuple, Optional
from urllib.parse import urlparse

import requests
import xmltodict
from bs4 import BeautifulSoup

from apps.bot.api.subscribe_service import SubscribeService
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.utils.video.downloader import VideoDownloader
from apps.bot.utils.video.muxer import AudioVideoMuxer


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
        video_content, audio_content = self._get_download_urls(player_url)
        if audio_content is not None:
            avm = AudioVideoMuxer()
            return avm.mux(video_content, audio_content)
        return video_content

    def _get_player_url(self, url: str) -> str:
        r = requests.get(url, headers=self.headers)
        bs4 = BeautifulSoup(r.text, 'html.parser')
        og_video = bs4.find("meta", property="og:video")
        if not og_video:
            raise PWarning("К сожалению видео старое и скачать его не получится. "
                           "Поддерживаются видео с апреля-мая 2023 года")
        player_url = bs4.find("meta", property="og:video").attrs['content']
        return player_url

    def _get_download_urls(self, player_url: str) -> Tuple[bytes, Optional[bytes]]:
        r = requests.get(player_url, headers=self.headers)
        bs4 = BeautifulSoup(r.text, 'html.parser')
        js_code = bs4.select_one('body > script:nth-child(11)').text
        first_split = js_code.split('var playerParams = ')[1]
        second_split = first_split.split('var container')[0]
        replacements = second_split.strip().replace(' ', '').replace('\n', '').replace(';', '')
        info = json.loads(replacements)
        info = info.get('params')[0]
        dash_webm = info.get('dash_webm')
        dash_sep = info.get('dash_sep')
        hls = info.get('hls')
        if dash_webm:
            return self._get_video_audio_dash(dash_webm)
        elif dash_sep:
            return self._get_video_audio_dash(dash_sep)
        else:
            return self._get_video_hls(hls)

    def _get_video_audio_dash(self, dash_webm_url) -> Tuple[bytes, bytes]:
        parsed_url = urlparse(dash_webm_url)

        r = requests.get(dash_webm_url, headers=self.headers).content
        dash_webm_dict = xmltodict.parse(r)
        adaptation_sets = dash_webm_dict['MPD']['Period']['AdaptationSet']

        video_representations = adaptation_sets[0]['Representation']
        video_representations = list(sorted(video_representations, key=lambda x: int(x['@bandwidth'])))

        audio_representations = adaptation_sets[1]['Representation']
        audio_representations = list(sorted(audio_representations, key=lambda x: int(x['@bandwidth'])))

        audio_url = f"{parsed_url.scheme}://{parsed_url.hostname}/{audio_representations[-1]['BaseURL']}"
        video_url = f"{parsed_url.scheme}://{parsed_url.hostname}/{video_representations[-1]['BaseURL']}"

        video_content = requests.get(video_url, headers=self.headers).content
        audio_content = requests.get(audio_url, headers=self.headers).content
        return video_content, audio_content

    @staticmethod
    def _get_video_hls(hls_url) -> tuple[bytes, None]:
        vd = VideoDownloader()
        return vd.download(hls_url, threads=10), None

    def get_video_info(self, url) -> dict:
        content = requests.get(url, headers=self.headers).content
        bs4 = BeautifulSoup(content, 'html.parser')
        try:
            if "clip-" in url:
                a_tag = bs4.select_one('.ui_crumb')
                return {
                    'channel_id': f"@{a_tag.attrs['href'].split('/')[-1]}",
                    'video_id': urlparse(url).path.split('clip')[1],
                    'channel_title': a_tag.text,
                    'video_title': bs4.find('meta', property="og:title").attrs['content'],
                }

            a_tag = bs4.select_one(".VideoCard__additionalInfo a")
            return {
                'channel_id': a_tag.attrs['href'].split('/')[-1],
                'video_id': urlparse(url).path.split('video')[1],
                'channel_title': a_tag.text,
                'video_title': bs4.find('meta', property="og:title").attrs['content'],
            }
        except:
            return {}

    def get_data_to_add_new_subscribe(self, url: str) -> dict:
        content = requests.get(url, headers=self.headers).content
        bs4 = BeautifulSoup(content, "html.parser")
        title = bs4.select_one(".VideoCard__ownerLink").text
        if 'playlist' in url:
            _playlist_id = url.rsplit('_', 1)[1]
            videos = bs4.find('div', {'id': f"video_subtab_pane_playlist_{_playlist_id}"}) \
                .find_all('div', {'class': 'VideoCard__info'})
            show_name = bs4.find("title").text.split(" | ", 1)[0]
            title = f"{title} | {show_name}"
        else:
            videos = bs4.find('div', {'id': "video_subtab_pane_all"}).find_all('div', {'class': 'VideoCard__info'})
        last_video = videos[0]
        last_video_id = last_video.find("a", {"class": "VideoCard__title"}).attrs['data-id']

        channel_id = bs4.select_one('.VideoCard__additionalInfo a').attrs['href'].split('/')[-1]
        playlist_id = urlparse(url).path.split('/', 2)[2]

        return {
            'channel_id': channel_id,
            'title': title,
            'last_video_id': last_video_id,
            'playlist_id': playlist_id if channel_id != playlist_id else None
        }

    def get_filtered_new_videos(self, channel_id: str, last_video_id: str, **kwargs) -> dict:
        if kwargs.get('playlist_id'):
            channel_id = kwargs['playlist_id']
        url = f"{self.URL}/{channel_id}"
        content = requests.get(url, headers=self.headers).content
        bs4 = BeautifulSoup(content, "html.parser")

        if 'playlist' in url:
            playlist_id = url.rsplit('_', 1)[1]
            videos = bs4.find('div', {'id': f"video_subtab_pane_playlist_{playlist_id}"}) \
                .find_all('div', {'class': 'VideoCard__info'})
        else:
            videos = bs4.find('div', {'id': "video_subtab_pane_all"}).find_all('div', {'class': 'VideoCard__info'})

        ids = [video.find('a', {'class': 'VideoCard__title'}).attrs['data-id'] for video in videos]
        titles = [video.select_one('.VideoCard__title').text.strip() for video in videos]

        if last_video_id:
            try:
                index = ids.index(last_video_id)
                ids = ids[:index]
                titles = titles[:index]
            except IndexError:
                pass

        ids = list(reversed(ids))
        titles = list(reversed(titles))
        urls = [f"{self.URL}{x}" for x in ids]

        return {"ids": ids, "titles": titles, "urls": urls}