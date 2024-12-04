import logging
import time

from django.core.management import BaseCommand

from apps.bot.api.media.vk.video import VKVideo
from apps.bot.api.media.youtube.video import YoutubeVideo
from apps.bot.api.subscribe_service import SubscribeServiceNewVideosData, SubscribeService
from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.const.exceptions import PSubscribeIndexError
from apps.bot.classes.event.event import Event
from apps.bot.classes.messages.message import Message
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.bot.commands.media.service import MediaService, MediaServiceResponse, MediaKeys
from apps.bot.commands.media.services.vk_video import VKVideoService
from apps.bot.commands.media.services.youtube_video import YoutubeVideoService
from apps.service.models import Subscribe, SubscribeItem

logger = logging.getLogger('subscribe_notifier')


class Command(BaseCommand):
    SERVICE_CLASS = {
        Subscribe.SERVICE_YOUTUBE: YoutubeVideo,
        Subscribe.SERVICE_VK: VKVideo,
    }
    SERVICE_MEDIA_METHOD = {
        Subscribe.SERVICE_YOUTUBE: YoutubeVideoService,
        Subscribe.SERVICE_VK: VKVideoService,
    }

    def handle(self, *args, **kwargs):

        logger.debug({
            "message": "handle"
        })
        sub_items = SubscribeItem.objects.all()

        for sub_item in sub_items:
            sub_class = self.SERVICE_CLASS[sub_item.service]
            media_service = self.SERVICE_MEDIA_METHOD[sub_item.service]
            try:
                self.check_video(sub_item, sub_class, media_service)
            except Exception:
                logger.exception({
                    "message": "Ошибка в проверке/отправке подписки",
                    "notify_enitity": sub_item.__dict__,
                })
        logger.debug({
            "message": "end handle"
        })

    def check_video(
            self,
            sub_item: SubscribeItem,
            sub_class: type[SubscribeService],
            media_service: type[MediaService]
    ):
        """
        Проверка на добавление новых видео на каналы/плейлисты
        """
        api = sub_class()
        try:
            new_videos = api.get_filtered_new_videos(
                sub_item.channel_id,
                sub_item.last_videos_id,
                playlist_id=sub_item.playlist_id
            )
        except PSubscribeIndexError as e:
            if e.args[0]:
                sub_item.last_videos_id = e.args[0]
                sub_item.save()
            raise

        if not new_videos.videos:
            return

        self.send_video(sub_item, new_videos, media_service=media_service)

    def send_video(
            self,
            sub_item: SubscribeItem,
            videos: SubscribeServiceNewVideosData,
            media_service: type[MediaService]
    ):
        logger.debug({
            "message": "send_file_or_video",
            "notify_enitity": sub_item.__dict__,
        })
        messages_with_att = []
        subscribes = sub_item.subscribes.all()
        for video in videos.videos:
            media_response = self.get_media_service_response(
                video.url,
                media_service,
                force_cache=sub_item.force_cache,
                high_resolution=sub_item.high_resolution
            )
            messages_with_att.append((media_response, video))

        for sub in subscribes:
            for media_response, video in messages_with_att:
                self.send_notify(sub_item, sub, video.title, video.url, media_response)
                time.sleep(1)

        if sub_item.save_to_disk:
            media_response = messages_with_att[0][0]
            video_title = messages_with_att[0][1].title
            self._save_to_disk(media_response, str(sub_item), video_title)

        sub_item.last_videos_id = sub_item.last_videos_id + videos.ids
        sub_item.save()

        logger.debug({
            "message": "end send_file_or_video",
            "notify_enitity": sub_item.__dict__,
        })

    @staticmethod
    def get_media_service_response(
            url: str,
            service_class: type[MediaService],
            high_resolution: bool = False,
            force_cache: bool = False,
    ) -> MediaServiceResponse:
        """
        Получение результата от медиа сервиса, проставление file_id
        """

        bot = TgBot()
        event = Event()
        event.message = Message()

        media_keys_list = []
        if high_resolution:
            media_keys_list.append(MediaKeys.HIGH_RESOLUTION_KEYS[0])
        if force_cache:
            media_keys_list.append(MediaKeys.FORCE_CACHE_KEYS[0])
        media_keys = MediaKeys(media_keys_list)

        logger.debug({
            "message": "get_media_result_msg",
            "notify_enitity": url,
        })
        service = service_class(bot, event, media_keys=media_keys, has_command_name=True)
        response: MediaServiceResponse = service.get_content_by_url(url)

        if response.attachments:
            att = response.attachments[0]
            if not att.file_id:
                att.set_file_id()
            if response.cache:
                att.content = None
            response.attachments = [att]

        logger.debug({
            "message": "end get_media_result_msg",
            "notify_enitity": url,
        })
        return response

    @staticmethod
    def send_notify(
            sub_item: SubscribeItem,
            sub: Subscribe,
            title: str,
            url: str,
            media_response: MediaServiceResponse
    ):
        logger.debug({
            "message": "send_notify",
            "notify_enitity": url,
        })
        bot = TgBot()

        if sub_item.playlist_title:
            answer = f"Новое видео в плейлисте {sub_item.playlist_title} канала {sub_item.channel_title}"
        else:
            answer = f"Новое видео на канале {sub_item.channel_title}"

        answer += f"\n\n{media_response.text}"
        answer = answer.replace(title, bot.get_formatted_url(title, url))
        rmi = ResponseMessageItem(
            text=answer,
            peer_id=sub.peer_id,
            message_thread_id=sub.message_thread_id,
            attachments=media_response.attachments
        )
        bot.send_response_message_item(rmi)
        logger.info(f"Отправил уведомление по подписке с id={sub.pk}")
        logger.debug({
            "message": "end send_notify",
            "notify_enitity": url,
        })

    @staticmethod
    def _save_to_disk(
            media_response: MediaServiceResponse,
            show_name: str,
            series_name: str
    ):
        logger.debug({
            "message": "_save_to_disk",
            "notify_enitity": show_name,
        })

        MediaService.save_to_disk(media_response, show_name, series_name)

        logger.debug({
            "message": "end _save_to_disk",
            "notify_enitity": show_name,
        })
