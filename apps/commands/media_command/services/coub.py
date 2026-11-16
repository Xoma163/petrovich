import json

import requests
from bs4 import BeautifulSoup

from apps.commands.media_command.service import MediaServiceResponse, MediaService
from apps.connectors.utils import get_default_headers
from apps.shared.exceptions import PWarning


class CoubService(MediaService):
    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        headers = get_default_headers()
        content = requests.get(url, headers=headers).content
        bs4 = BeautifulSoup(content, "html.parser")
        video_data = bs4.find("script", {"id": "coubPageCoubJson"})
        if video_data is None:
            raise PWarning("Coub не вернул данные видео. Проверьте ссылку и доступ к публикации")
        try:
            data = json.loads(video_data.text)
            video_url = data["file_versions"]["share"]["default"]
            title = data["title"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise PWarning("Не удалось прочитать данные видео Coub. Попробуйте позже") from exc
        if not isinstance(video_url, str) or not video_url:
            raise PWarning("Coub не вернул ссылку на видео. Попробуйте позже")
        video = self.bot.get_video_attachment(
            url=video_url,
            peer_id=self.event.peer_id,
            message_thread_id=self.event.message_thread_id,
        )
        return MediaServiceResponse(text=title, attachments=[video])

    @classmethod
    def urls(cls) -> list[str]:
        return ["coub.com"]
