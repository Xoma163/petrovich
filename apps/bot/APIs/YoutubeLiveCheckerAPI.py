"""
GET https://youtube.googleapis.com/youtube/v3/liveBroadcasts?broadcastStatus=active&broadcastType=all&key=[YOUR_API_KEY] HTTP/1.1

Authorization: Bearer [YOUR_ACCESS_TOKEN]
Accept: application/json

"""

import google_auth_oauthlib
import google_auth_oauthlib.flow
import googleapiclient
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from petrovich.settings import BASE_DIR


class YoutubeLiveCheckerAPI:
    SECRET_FILE = f"{BASE_DIR}/secrets/google.json"
    SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

    def __init__(self):
        pass

    def get_stream_info_if_online(self):
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(self.SECRET_FILE, self.SCOPES)
        # credentials = flow.run_console(access_type="offline")
        credentials = Credentials(
            None,
            refresh_token=flow.client_config['refresh_token'],
            token_uri="https://accounts.google.com/o/oauth2/token",
            client_id=flow.client_config['client_id'],
            client_secret=flow.client_config['client_secret']
        )
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

        request = youtube.liveBroadcasts() \
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
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'chat_url_1': f"https://studio.youtube.com/live_chat?v={item['id']}",
                'chat_url_2': f"https://www.youtube.com/live_chat?v={item['id']}"
            }
            return resp
