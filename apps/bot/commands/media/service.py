import dataclasses
import os
import shutil
from io import BytesIO

from apps.bot.classes.bots.bot import Bot
from apps.bot.classes.event.event import Event
from apps.bot.classes.messages.attachments.attachment import Attachment
from apps.bot.utils.utils import prepare_filename
from apps.service.models import VideoCache
from petrovich.settings import MAIN_SITE, env


@dataclasses.dataclass
class MediaServiceResponse:
    text: str | None = None
    attachments: list[Attachment] | None = None
    cache: VideoCache | None = None
    cache_url: str | None = None
    video_title: str | None = None


class MediaService:
    def __init__(self, bot: Bot, event: Event):
        self.bot: Bot = bot
        self.event: Event = event
        self.activity = None

    HIGH_KEYS = {'high', 'best'}

    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        """
        Основной метод сервиса, который отдаёт содержимое и текст
        """
        raise NotImplementedError

    def check_valid_url(self, url: str) -> None:
        """
        Проверка на валидный урл
        """
        pass

    def check_sender_role(self) -> None:
        """
        Проверка на роль пользователя
        """
        pass

    @classmethod
    def urls(cls) -> list[str]:
        """
        Список всех урлов (hostnames) на которые должен откликаться сервис
        """
        raise NotImplementedError

    def _get_cached(self, channel_id, video_id, title) -> MediaServiceResponse | None:
        """
        Получение кэшированного видео
        """
        try:
            cache = VideoCache.objects.get(channel_id=channel_id, video_id=video_id)
            text = self._get_download_cache_text(title, cache.video.url)
            return MediaServiceResponse(text, None, cache=cache, cache_url=self._get_cached_url(cache.video.url),
                                        video_title=title)
        except VideoCache.DoesNotExist:
            return None

    def _cache_video(
            self,
            channel_id: str,
            video_id: str,
            title: str,
            content: bytes
    ) -> MediaServiceResponse:
        """
        Сохранение видео в кэш
        """

        filename = f"{title}.mp4"
        filename = prepare_filename(filename)

        cache = VideoCache(
            channel_id=channel_id,
            video_id=video_id,
            filename=filename
        )
        cache.video.save(filename, content=BytesIO(content))
        cache.save()
        text = self._get_download_cache_text(title, cache.video.url)
        return MediaServiceResponse(text, None, cache=cache, cache_url=self._get_cached_url(cache.video.url),
                                    video_title=title)

    def _get_download_cache_text(self, title, cache_video_url):
        return f"{title}\nСкачать можно здесь {self.bot.get_formatted_url('здесь', self._get_cached_url(cache_video_url))}"

    @staticmethod
    def _get_cached_url(cache_video_url: str) -> str:
        return MAIN_SITE + cache_video_url

    @classmethod
    def save_to_disk(cls, media_response: MediaServiceResponse, folder: str, filename: str):
        path = env.str('DISK_SAVE_PATH')

        show_name_correct = prepare_filename(str(folder))
        series_name_correct = prepare_filename(str(filename))

        show_folder = os.path.join(path, show_name_correct)
        if not os.path.exists(show_folder):
            os.makedirs(show_folder)
        full_path = os.path.join(show_folder, f"{series_name_correct}.mp4")

        if media_response.cache:
            shutil.copyfile(media_response.cache.video.path, os.path.join(str(show_folder), full_path))
        else:
            with open(full_path, 'wb') as f:
                f.write(media_response.attachments[0].content)
