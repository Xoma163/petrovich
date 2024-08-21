import random
from urllib.parse import urlparse

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import AcceptExtraMixin
from apps.bot.classes.const.consts import Role, Platform
from apps.bot.classes.const.exceptions import PWarning, PSkip
from apps.bot.classes.event.event import Event
from apps.bot.classes.help_text import HelpText, HelpTextArgument, HelpTextKey, HelpTextItem
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.link import LinkAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.commands.media.service import MediaService, MediaServiceResponse, MediaKeys
from apps.bot.commands.media.services.coub import CoubService
from apps.bot.commands.media.services.instagram import InstagramService
from apps.bot.commands.media.services.pinterest import PinterestService
from apps.bot.commands.media.services.reddit import RedditService
from apps.bot.commands.media.services.spotify import SpotifyService
from apps.bot.commands.media.services.suno_ai import SunoAIService
from apps.bot.commands.media.services.tiktok import TikTokService
from apps.bot.commands.media.services.twitch_clips import TwitchClipsService
from apps.bot.commands.media.services.twitter import TwitterService
from apps.bot.commands.media.services.vk_video import VKVideoService
from apps.bot.commands.media.services.yandex_music import YandexMusicService
from apps.bot.commands.media.services.youtube_music import YoutubeMusicService
from apps.bot.commands.media.services.youtube_video import YoutubeVideoService
from apps.bot.commands.media.services.zen import ZenService
from apps.bot.utils.utils import get_urls_from_text, get_flat_list, markdown_wrap_symbols
from apps.bot.utils.video.video_handler import VideoHandler


class Media(AcceptExtraMixin):
    name = "медиа"
    names = ["media"]

    help_text = HelpText(
        commands_text="скачивает видео/фото из соцсетей и присылает его",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextArgument("(ссылка на видео/пост)", "скачивает видео из соцсетей и присылает его")
            ])
        ],
        help_text_keys=[
            HelpTextItem(Role.USER, [
                HelpTextKey(MediaKeys.NO_MEDIA_KEYS[0], MediaKeys.NO_MEDIA_KEYS[1:], "позволяет не запускать команду"),
                HelpTextKey(MediaKeys.AUDIO_KEYS[0], MediaKeys.AUDIO_KEYS[1:],
                            "позволяет скачивать аудиодорожку для видео"),
                HelpTextKey(MediaKeys.HIGH_KEYS[0], MediaKeys.HIGH_KEYS[1:],
                            "сохраняет видео в максимальном качестве (VK Video/Youtube Video)"),
                HelpTextKey(MediaKeys.CACHE_KEYS[0], MediaKeys.CACHE_KEYS[1:],
                            "позволяет загрузить видео в онлайн-кэш (VK Video/Youtube Video)"),
                HelpTextKey(MediaKeys.FORCE_KEYS[0], MediaKeys.FORCE_KEYS[1:],
                            "позволяет загрузить видео принудительно (Youtube Video)"),
                HelpTextKey(MediaKeys.THREADS_KEYS[0], MediaKeys.THREADS_KEYS[1:],
                            "позволяет скачивать пост с комментариями автора(Twitter)"),
            ]),
            HelpTextItem(Role.ADMIN, [
                HelpTextKey(MediaKeys.DISK_KEYS[0], MediaKeys.DISK_KEYS[1:], "сохраняет видео в локальную директорию"),
            ]),

        ],
        extra_text=(
            "Поддерживаемые соцсети: Youtube Video/Youtube Music/Reddit/TikTok/Instagram/Twitter/"
            "Yandex Music/Pinterest/Coub/VK Video/TwitchClips/Spotify/Suno AI/Yandex Zen\n\n"

            "Некоторые сервисы доступны только доверенным пользователям: Twitter/Instagram/Yandex Music\n"
            "По умолчанию видео для Youtube/VK Video качается в качестве до 1080p\n"
            "Видосы из ютуба в чате качаются автоматически только если длина ролика менее 2 минут\n"
            "Если у бота есть доступ к переписке, то достаточно прислать только ссылку"
        )
    )

    platforms = [Platform.TG]
    attachments = [LinkAttachment]

    bot: TgBot

    SERVICES = [
        YoutubeVideoService,
        YoutubeMusicService,
        VKVideoService,
        TikTokService,
        RedditService,
        InstagramService,
        TwitterService,
        YandexMusicService,
        PinterestService,
        CoubService,
        TwitchClipsService,
        SpotifyService,
        SunoAIService,
        ZenService,
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_command_name = None

    @classmethod
    def all_urls(cls) -> list[str]:
        return get_flat_list([x.urls() for x in cls.SERVICES])

    @classmethod
    def accept_extra(cls, event: Event) -> bool:
        if event.message and not event.message.mentioned:
            media_keys = MediaKeys(event.message.keys)
            if media_keys.no_media:
                return False
            all_urls = get_urls_from_text(event.message.clear_case)
            for url in all_urls:
                message_is_media_link = urlparse(url).hostname in cls.all_urls()
                if message_is_media_link:
                    return True
        return False

    def start(self) -> ResponseMessage:
        source = self._get_source_link()
        media_keys = MediaKeys(self.event.message.keys)

        service_class, chosen_url = self._get_service_and_chosen_url(source)
        service = service_class(self.bot, self.event, media_keys=media_keys, has_command_name=self.has_command_name)
        service.check_sender_role()
        service.check_valid_url(chosen_url)

        try:
            media_response = service.get_content_by_url(chosen_url)
        except PWarning as e:
            # Если была вызвана команда или отправлено сообщение в лс
            if self.has_command_name or self.event.is_from_pm:
                raise e
            # Иначе не отправляем сообщение
            else:
                raise PSkip()

        att_is_video = media_response.attachments and isinstance(media_response.attachments[0], VideoAttachment)

        if media_keys.disk and att_is_video:
            self.check_sender(Role.ADMIN)
            title = media_response.video_title or str(random.randint(1000000000, 999999999))
            service.save_to_disk(media_response, "Скачано", title)

        if media_keys.audio and att_is_video:
            video: VideoAttachment = media_response.attachments[0]
            vh = VideoHandler(video=video)
            aa = AudioAttachment()
            aa.title = media_response.video_title
            aa.content = vh.get_audio_track()
            aa.thumbnail_url = video.thumbnail_url
            media_response.attachments[0] = aa

        return self.prepare_media_response(media_response, chosen_service=service_class, chosen_url=chosen_url)

    def _get_service_and_chosen_url(self, source) -> tuple[type[MediaService], str]:
        """
        Проверяет входные ссылки на принадлежность к какому-либо сервису
        Возвращает сервис и выбранную ссылку
        """

        hostname = urlparse(source).hostname
        for service in self.SERVICES:
            if hostname in service.urls():
                return service, source
        raise PWarning("Не медиа ссылка")

    def _get_extra_text(self, chosen_url) -> str:
        """
        Пользователь присылает ссылку и дополнительный текст.
        Этот метод вытягивает этот дополнительный текст
        """

        if self.has_command_name:
            args_str = " ".join(self.event.message.args_case[1:])
        else:
            args_str = self.event.message.raw

        index = args_str.find(chosen_url)
        extra_text = f"{args_str[:index].strip()}\n{args_str[index + len(chosen_url):].strip()}"
        extra_text = extra_text if extra_text.strip() else ""
        for key in self.event.message.keys:
            for key_symbol in self.event.message.KEYS_SYMBOLS:
                full_key = key_symbol + key
                if (index := extra_text.find(full_key)) != -1:
                    extra_text = f"{extra_text[:index].strip()}\n{extra_text[index + len(full_key):].strip()}"

        extra_text = extra_text if extra_text.strip() else ""
        return extra_text

    def prepare_media_response(
            self,
            media_response: MediaServiceResponse,
            chosen_service: type[MediaService],
            chosen_url: str
    ) -> ResponseMessage:
        text = media_response.text or ""

        answer = ""
        if text:
            # NOT IN VK VIDEO
            if chosen_service not in [None]:
                answer = f"{markdown_wrap_symbols(text)}\n"
            else:
                answer = text

        if extra_text := self._get_extra_text(chosen_url):
            if text != extra_text.strip():
                answer += f"\n{extra_text}\n"

        if self.event.is_from_chat:
            answer += f"\nОт {self.event.sender}"

        source_hostname = str(urlparse(chosen_url).hostname).lstrip('www.')
        answer += f'\nИсточник: {self.bot.get_formatted_url(source_hostname, chosen_url)}'
        answer = answer.strip()

        reply_to = self.event.fwd[0].message.id if self.event.fwd else None

        rmi = ResponseMessageItem(
            text=answer,
            attachments=media_response.attachments,
            reply_to=reply_to,
            peer_id=self.event.peer_id,
            message_thread_id=self.event.message_thread_id
        )
        br = self.bot.send_response_message_item(rmi)
        if br.success:
            self.bot.delete_messages(self.event.peer_id, self.event.message.id)
        return ResponseMessage(rmi, send=False)

    def _get_source_link(self) -> str:
        """
        Ищет ссылки в присланном тексте
        """

        if self.event.message.command in self.full_names:
            self.has_command_name = True
            if not self.event.message.args and not self.event.fwd:
                raise PWarning("Для работы команды требуются аргументы или пересылаемые сообщения")
        else:
            self.has_command_name = False
        return self.event.get_all_attachments([LinkAttachment])[0].url


"""

# def _remove_trim_args(self, url, end_pos):
#     yt_api = YoutubeVideo()
#     raw_list = self.event.message.raw.split(' ')
#
#     index = 1
#     if self.has_command_name:
#         index += 1
#
#     if yt_api.get_timecode_str(url):
#         if end_pos:
#             del raw_list[index]
#     else:
#         if end_pos:
#             del raw_list[index + 1]
#             del raw_list[index]
#         else:
#             del raw_list[index]
#     raw = " ".join(raw_list)
#     self.event.message = Message(raw, _id=self.event.message.id)

# try:
#     pass
# except PWarning as e:
#     button = self.bot.get_button("Повторить", command=self.name, args=[url])
#     keyboard = self.bot.get_inline_keyboard([button])
#     raise PWarning(e.msg, keyboard=keyboard)


"""
