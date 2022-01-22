import os
import pickle

import googleapiclient.discovery
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from petrovich.settings import BASE_DIR


class YoutubeLiveCheckerAPI:
    SECRET_FILE = f"{BASE_DIR}/secrets/google.json"
    CREDENTIALS_PICKLE_FILE = f"{BASE_DIR}/secrets/google.pkl"
    SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

    def __init__(self):
        credentials = None

        # youtube_data_token_brand.pickle stores the user's credentials from previously successful logins
        if os.path.exists(self.CREDENTIALS_PICKLE_FILE):
            with open(self.CREDENTIALS_PICKLE_FILE, 'rb') as token:
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
                    scopes=[
                        'https://www.googleapis.com/auth/youtube.readonly'
                    ]
                )

                flow.run_local_server(port=8080, prompt='consent', authorization_prompt_message='')
                credentials = flow.credentials

                # Save the credentials for the next run
                with open(self.CREDENTIALS_PICKLE_FILE, 'wb') as f:
                    print('Saving Credentials for Future Use...')
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
