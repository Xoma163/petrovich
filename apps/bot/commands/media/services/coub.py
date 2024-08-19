import json

import requests
from bs4 import BeautifulSoup

from apps.bot.commands.media.service import MediaServiceResponse, MediaService
from apps.bot.utils.utils import get_default_headers


class CoubService(MediaService):

    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        headers = get_default_headers()
        content = requests.get(url, headers=headers).content
        bs4 = BeautifulSoup(content, "html.parser")
        data = json.loads(bs4.find("script", {'id': 'coubPageCoubJson'}).text)
        video_url = data['file_versions']['share']['default']
        video = self.bot.get_video_attachment(video_url, peer_id=self.event.peer_id)
        title = data['title']
        return MediaServiceResponse(text=title, attachments=[video])

    @classmethod
    def urls(cls) -> list[str]:
        return ['coub.com']
