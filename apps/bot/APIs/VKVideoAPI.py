import json
import os
from tempfile import NamedTemporaryFile
from typing import Tuple, Optional
from urllib.parse import urlparse

import requests
import xmltodict
import yt_dlp
from bs4 import BeautifulSoup

from apps.bot.utils.AudioVideoMuxer import AudioVideoMuxer
from apps.bot.utils.DoTheLinuxComand import do_the_linux_command
from apps.bot.utils.NothingLogger import NothingLogger


class VKVideoAPI:
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

    def __init__(self, max_filesize_mb=None):
        self.title = None
        self.max_filesize_mb = max_filesize_mb

    def get_video(self, url):
        player_url = self._get_player_url(url)
        video_content, audio_content = self._get_download_urls(player_url)
        if audio_content:
            avm = AudioVideoMuxer()
            return avm.mux(video_content, audio_content)
        else:
            return video_content

    def _get_player_url(self, url: str) -> str:
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        player_url = soup.find("meta", property="og:video").attrs['content']
        self.title = soup.find("meta", property="og:title").attrs['content']
        return player_url

    def _get_download_urls(self, player_url: str) -> Tuple[bytes, Optional[bytes]]:
        response = requests.get(player_url, headers=self.headers)
        bs4 = BeautifulSoup(response.text, 'html.parser')
        js_code = bs4.select_one('body > script:nth-child(11)').text
        first_split = js_code.split('var playerParams = ')[1]
        second_split = first_split.split('var container')[0]
        replacements = second_split.strip().replace(' ', '').replace('\n', '').replace(';', '')
        info = json.loads(replacements)
        info = info.get('params')[0]
        dash_webm = info.get('dash_webm')
        hls = info.get('hls')
        if dash_webm:
            return self._get_video_autio_dash_webm(dash_webm)
        else:
            return self._get_video_hls(hls)

    def _get_video_autio_dash_webm(self, dash_webm_url) -> Tuple[bytes, bytes]:
        parsed_url = urlparse(dash_webm_url)

        response = requests.get(dash_webm_url, headers=self.headers).content
        dash_webm_dict = xmltodict.parse(response)
        adaptation_sets = dash_webm_dict['MPD']['Period']['AdaptationSet']

        video_representations = adaptation_sets[0]['Representation']
        audio_representations = adaptation_sets[1]['Representation']

        audio_url = f"{parsed_url.scheme}://{parsed_url.hostname}/{audio_representations[-1]['BaseURL']}"
        audio_content_length = float(requests.head(audio_url, headers=self.headers).headers['Content-Length'])
        audio_filesize = round(audio_content_length / 1024 / 1024, 2)

        video_url = None
        if self.max_filesize_mb:
            for video in reversed(video_representations):
                video_url = f"{parsed_url.scheme}://{parsed_url.hostname}/{video['BaseURL']}"
                video_content_length = float(
                    requests.head(video_url, headers=self.headers).headers['Content-Length'])
                video_filesize = round(video_content_length / 1024 / 1024, 2)

                if video_filesize + audio_filesize < self.max_filesize_mb:
                    break
        else:
            video_url = f"{parsed_url.scheme}://{parsed_url.hostname}/{video_representations[-1]['BaseURL']}"

        video_content = requests.get(video_url, headers=self.headers).content
        audio_content = requests.get(audio_url, headers=self.headers).content
        return video_content, audio_content

    @staticmethod
    def _get_video_hls(hls_url) -> tuple[bytes, None]:
        ydl_params = {
            'logger': NothingLogger()
        }
        ytdl = yt_dlp.YoutubeDL(ydl_params)
        info = ytdl.extract_info(hls_url, download=False)
        url = info['formats'][-1]['url']

        tmp_video_file = NamedTemporaryFile().name
        try:
            do_the_linux_command(f"yt-dlp -o {tmp_video_file} {url}")
            with open(tmp_video_file, 'rb') as file:
                video_content = file.read()
        finally:
            os.remove(tmp_video_file)
        return video_content, None

    def parse_channel(self, url):
        content = requests.get(url, headers=self.headers).content
        bs4 = BeautifulSoup(content, "html.parser")
        title = bs4.select_one('.VideoHeader__breadcrumbsEntity .VideoHeader__name').text
        if 'playlist' in url:
            playlist_id = url.rsplit('_', 1)[1]
            videos = bs4.find('div', {'id': f"video_subtab_pane_playlist_{playlist_id}"}) \
                .find_all('div', {'class': 'VideoCard__info'})
            show_name = bs4.select('.ui_crumb')[-1].text
            title = f"{title} | {show_name}"
        else:
            videos = bs4.find('div', {'id': "video_subtab_pane_all"}).find_all('div', {'class': 'VideoCard__info'})
        last_video = videos[0]
        last_video_id = last_video.find("a", {"class": "VideoCard__title"}).attrs['data-id']
        channel_id = urlparse(url).path.split('/', 2)[2]

        return {
            'title': title,
            'last_video_id': last_video_id,
            'channel_id': channel_id,
        }

    def get_video_info(self, url):
        content = requests.get(url, headers=self.headers).content
        bs4 = BeautifulSoup(content, 'html.parser')
        return {
            'channel_id': bs4.find('a', {'class': 'VideoSubheader__actionLink'}).attrs['href'].split('/')[2],
            'video_id': urlparse(url).path.split('video')[1],
            'channel_title': bs4.find('span', {'class': 'VideoHeader__name'}).text,
            'video_title': bs4.find('meta', property="og:title").attrs['content'],
        }

    def get_last_video_ids_with_titles(self, channel_id, last_video_id=None):
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
        return ids, titles
