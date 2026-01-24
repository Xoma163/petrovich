import dataclasses
import os
import shutil
from io import BytesIO
from urllib.parse import unquote

from apps.bot.core.bot.bot import Bot
from apps.bot.core.event.event import Event
from apps.bot.core.messages.attachments.attachment import Attachment
from apps.bot.utils.utils import prepare_filename
from apps.commands.media_command.models import VideoCache
from petrovich.settings import MAIN_SITE, env


@dataclasses.dataclass
class MediaServiceResponse:
    text: str | None = None
    attachments: list[Attachment] | None = None
    cache: VideoCache | None = None
    cache_url: str | None = None
    video_title: str | None = None
    need_to_wrap_html_tags: bool = True


class MediaKeys:
    NO_MEDIA_KEYS = ["nomedia", "no-media", 'n']
    AUDIO_ONLY_KEYS = ['audio', 'a']
    SAVE_TO_DISK_KEYS = ['save', 'disk', 's', 'd']
    HIGH_RESOLUTION_KEYS = ['high', 'best', 'h', 'b']
    FORCE_CACHE_KEYS = ['cache', 'c']
    FORCE_KEYS = ['force', 'f']
    SPOILER_KEYS = ['spoiler']

    def __init__(self, keys: list, short_keys: list):
        self.no_media: bool = self.check_key(keys, short_keys, self.NO_MEDIA_KEYS)
        self.audio_only: bool = self.check_key(keys, short_keys, self.AUDIO_ONLY_KEYS)
        self.save_to_disk: bool = self.check_key(keys, short_keys, self.SAVE_TO_DISK_KEYS)
        self.high_resolution: bool = self.check_key(keys, short_keys, self.HIGH_RESOLUTION_KEYS)
        self.force_cache: bool = self.check_key(keys, short_keys, self.FORCE_CACHE_KEYS)
        self.force: bool = self.check_key(keys, short_keys, self.FORCE_KEYS)
        self.spoiler: bool = self.check_key(keys, short_keys, self.SPOILER_KEYS)

    @staticmethod
    def check_key(keys_event: list, short_keys_event: list, keys_values: list) -> bool:
        keys = any(x in keys_event for x in keys_values)
        short_keys = any(x == y for x in keys_values for y in short_keys_event)
        return keys or short_keys


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
            text = self._get_download_cache_text(title, cache.video.url, cache.original_url)
            return MediaServiceResponse(
                text=text,
                attachments=None,
                cache=cache,
                cache_url=self._get_cached_url(cache.video.url),
                video_title=title
            )
        except VideoCache.DoesNotExist:
            return None

    def _cache_video(
            self,
            channel_id: str,
            video_id: str,
            title: str,
            original_url: str,
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
            filename=filename,
            original_url=original_url,
        )
        cache.video.save(filename, content=BytesIO(content))
        cache.save()
        text = self._get_download_cache_text(title, cache.video.url, cache.original_url)
        return MediaServiceResponse(
            text=text,
            attachments=None,
            cache=cache,
            cache_url=self._get_cached_url(cache.video.url),
            video_title=title
        )

    def _get_download_cache_text(self, title, cache_video_url, cache_video_original_url):
        url = unquote(cache_video_url)
        formatted_original_video_url = self.bot.get_formatted_url(title, cache_video_original_url)
        formatted_cached_video_url = self.bot.get_formatted_url('здесь', self._get_cached_url(url))
        return f"{formatted_original_video_url}\n" \
               f"Скачать можно {formatted_cached_video_url}"

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
