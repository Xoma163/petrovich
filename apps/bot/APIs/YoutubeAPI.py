import os
import pickle
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qsl

import googleapiclient.discovery
import requests
import yt_dlp
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PWarning, PSkip
from apps.bot.utils.NothingLogger import NothingLogger
from petrovich.settings import BASE_DIR


class YoutubeAPI:
    def __init__(self):
        self.title = None
        self.duration = 0

        self._youtube_api_client = None

    @staticmethod
    def get_timecode(url):
        return dict(parse_qsl(urlparse(url).query)).get('t')

    def get_timecode_str(self, url):
        t = self.get_timecode(url)
        if t:
            t = t[0].rstrip('s')
            h, m, s = str(timedelta(seconds=int(t))).split(":")
            return f"{m}:{s}"
        return None

    def get_last_video(self, channel_id):
        response = requests.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
        if response.status_code != 200:
            raise PWarning("Не нашёл такого канала")
        bsop = BeautifulSoup(response.content, 'html.parser')
        last_video = bsop.find_all('entry')[0]
        self.title = bsop.find('title').text
        return {
            'title': self.title,
            'last_video': {
                'title': last_video.find('title').text,
                'link': last_video.find('link').attrs['href'],
                'date': datetime.strptime(last_video.find('published').text, '%Y-%m-%dT%H:%M:%S%z'),
            }
        }

    def get_video_download_url(self, url, platform=None):
        ydl_params = {
            'outtmpl': '%(id)s%(ext)s',
            'logger': NothingLogger()
        }
        ydl = yt_dlp.YoutubeDL(ydl_params)
        ydl.add_default_info_extractors()

        try:
            video_info = ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError:
            raise PWarning("Не смог найти видео по этой ссылке")
        self.title = video_info['title']

        self.duration = video_info.get('duration')
        if not self.duration:
            raise PSkip()
        video_urls = [x for x in video_info['formats'] if x['ext'] == 'mp4' and x.get('asr')]
        videos = sorted(video_urls, key=lambda x: x['format_note'], reverse=True)
        if platform == Platform.TG:
            for video in videos:
                filesize = video.get('filesize') or video.get('filesize_approx')
                if filesize:
                    from apps.bot.classes.bots.tg.TgBot import TgBot

                    if filesize / 1024 / 1024 < TgBot.MAX_VIDEO_SIZE_MB:
                        max_quality_video = video
                        break
            else:
                raise PSkip()
        else:
            max_quality_video = videos[0]
        url = max_quality_video['url']
        return url

    def init_for_live_check(self):
        # SECRET_FILE = f"{BASE_DIR}/secrets/google.json"
        CREDENTIALS_PICKLE_FILE = f"{BASE_DIR}/secrets/google.pkl"
        SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

        credentials = None

        # youtube_data_token_brand.pickle stores the user's credentials from previously successful logins
        if os.path.exists(CREDENTIALS_PICKLE_FILE):
            with open(CREDENTIALS_PICKLE_FILE, 'rb') as token:
                credentials = pickle.load(token)

        # If there are no valid credentials available, then either refresh the token or log in.
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                print('Refreshing Access Token...')
                credentials.refresh(Request())
            else:
                print('Fetching New Tokens...')
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secrets_youtube_data_brand.json',
                    scopes=SCOPES
                )

                flow.run_local_server(port=8080, prompt='consent', authorization_prompt_message='')
                credentials = flow.credentials

                # Save the credentials for the next run
                with open(CREDENTIALS_PICKLE_FILE, 'wb') as f:
                    print('Saving Credentials for Future Use...')
                    pickle.dump(credentials, f)
        self._youtube_api_client = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

    def get_stream_info_if_online(self):
        if self._youtube_api_client is None:
            self.init_for_live_check()

        request = self._youtube_api_client.liveBroadcasts() \
            .list(
            broadcastStatus="active",
            broadcastType="all",
            part="snippet"
        )
        response = request.execute()
        if not response['items']:
            return False
        else:
            item = response["items"][0]
            resp = {
                'video_url': f"https://youtu.be/{item['id']}",
                'full_video_url': f"https://www.youtube.com/watch?v={item['id']}",
                'embed_video_url': f"https://www.youtube.com/embed/{item['id']}",
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'chat_url_1': f"https://studio.youtube.com/live_chat?v={item['id']}",
                'chat_url_2': f"https://www.youtube.com/live_chat?v={item['id']}"
            }
            return resp
