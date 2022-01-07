import os
import pickle

import google_auth_oauthlib.flow
import googleapiclient.discovery

from petrovich.settings import BASE_DIR


class YoutubeLiveCheckerAPI:
    SECRET_FILE = f"{BASE_DIR}/secrets/google.json"
    CREDENTIALS_PICKLE_FILE = f"{BASE_DIR}/secrets/google.pkl"
    SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

    def __init__(self):
        if os.path.exists(self.CREDENTIALS_PICKLE_FILE):
            with open(self.CREDENTIALS_PICKLE_FILE, 'rb') as f:
                credentials = pickle.load(f)
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(self.SECRET_FILE, self.SCOPES)
            credentials = flow.run_console(access_type="offline", prompt="consent")
            with open(self.CREDENTIALS_PICKLE_FILE, 'wb') as f:
                pickle.dump(credentials, f)

        self.youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

    def get_stream_info_if_online(self):
        request = self.youtube.liveBroadcasts() \
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
