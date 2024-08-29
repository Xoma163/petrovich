import dataclasses
import os
import shutil
from io import BytesIO
from urllib.parse import unquote

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


class MediaKeys:
    NO_MEDIA_KEYS = ["nomedia", "no-media", 'n']
    AUDIO_KEYS = ['audio', 'a']
    DISK_KEYS = ['save', 'disk', 's', 'd']
    HIGH_KEYS = ['high', 'best', 'h', 'b']
    CACHE_KEYS = ['cache', 'c']
    FORCE_KEYS = ['force', 'f']
    THREADS_KEYS = ['thread', 'threads', 'with-threads', 'тред', 'треды', 't']

    def __init__(self, keys: list):
        self.no_media: bool = self.check_key(keys, self.NO_MEDIA_KEYS)
        self.audio: bool = self.check_key(keys, self.AUDIO_KEYS)
        self.disk: bool = self.check_key(keys, self.DISK_KEYS)
        self.high: bool = self.check_key(keys, self.HIGH_KEYS)
        self.cache: bool = self.check_key(keys, self.CACHE_KEYS)
        self.force: bool = self.check_key(keys, self.FORCE_KEYS)
        self.threads: bool = self.check_key(keys, self.THREADS_KEYS)

    @staticmethod
    def check_key(keys_event: list, keys_values: list) -> bool:
        return any(x in keys_event for x in keys_values)


class MediaService:
    def __init__(self, bot: Bot, event: Event, media_keys: MediaKeys, has_command_name: bool):
        self.bot: Bot = bot
        self.event: Event = event
        self.media_keys: MediaKeys = media_keys
        self.has_command_name: bool = has_command_name
        self.activity = None

    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        """
        Основной метод сервиса, который отдаёт содержимое и текст
        """
        raise NotImplementedError

    def check_valid_url(self, url: str) -> None:
        """
        Проверка на валидный урл
        """

    def check_sender_role(self) -> None:
        """
        Проверка на роль пользователя
        """

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
        url = unquote(cache_video_url)
        return f"{title}\nСкачать можно {self.bot.get_formatted_url('здесь', self._get_cached_url(url))}"

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
