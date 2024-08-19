import logging
import time
from itertools import groupby

from django.core.management import BaseCommand

from apps.bot.api.media.vk.video import VKVideo
from apps.bot.api.media.youtube.video import YoutubeVideo
from apps.bot.api.subscribe_service import SubscribeServiceNewVideosData, SubscribeService
from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.const.exceptions import PSubscribeIndexError
from apps.bot.classes.event.event import Event
from apps.bot.classes.messages.message import Message
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.bot.commands.media.service import MediaService, MediaServiceResponse
from apps.bot.commands.media.services.vk_video import VKVideoService
from apps.bot.commands.media.services.youtube_video import YoutubeVideoService
from apps.service.models import Subscribe

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
        """
        Группирование по каналам, чтобы сразу отправлять некоторые подписки вместе для экономии ресурсов
        """

        logger.debug({
            "message": "handle"
        })
        subs = Subscribe.objects.all()
        groupped_subs = groupby(subs.order_by("channel_id"), lambda x: (x.service, x.channel_id, x.playlist_id))

        for (service, _, _), subs in groupped_subs:
            sub_class = self.SERVICE_CLASS[service]
            media_service = self.SERVICE_MEDIA_METHOD[service]
            subs = list(subs)
            try:
                self.check_video(subs, sub_class, media_service)
            except Exception:
                logger.exception({
                    "message": "Ошибка в проверке/отправке подписки",
                    "notify_enitity": subs[0].__dict__,
                })
        logger.debug({
            "message": "end handle"
        })

    def check_video(self, subs: list[Subscribe], sub_class: type[SubscribeService], media_service: type[MediaService]):
        """
        Проверка на добавление новых видео на каналы/плейлисты
        """

        if len(set(x.last_videos_id[-1] for x in subs)) == 1:
            api = sub_class()
            try:
                new_videos = api.get_filtered_new_videos(
                    subs[0].channel_id,
                    subs[0].last_videos_id,
                    playlist_id=subs[0].playlist_id
                )
            except PSubscribeIndexError as e:
                for sub in subs:
                    if e.args[0]:
                        sub.last_videos_id = e.args[0]
                        sub.save()
                raise

            if not new_videos.videos:
                return

            self.send_video(subs, new_videos, media_service=media_service)
        else:
            for sub in subs:
                self.check_video([sub], sub_class, media_service)

    def send_video(
            self,
            subs: list[Subscribe],
            videos: SubscribeServiceNewVideosData,
            media_service: type[MediaService]
    ):
        logger.debug({
            "message": "send_file_or_video",
            "notify_enitity": subs[0].__dict__,
        })
        messages_with_att = []
        high_res = any([sub.high_resolution for sub in subs])
        for video in videos.videos:
            media_response = self.get_media_service_response(video.url, media_service, high_res=high_res)
            messages_with_att.append((media_response, video))

        for sub in subs:
            for media_response, video in messages_with_att:
                self.send_notify(sub, video.title, video.url, media_response)

                if sub.save_to_disk:
                    self._save_to_disk(media_response, str(sub), video.title, )

                time.sleep(1)
            sub.last_videos_id = sub.last_videos_id + videos.ids
            sub.save()

        logger.debug({
            "message": "end send_file_or_video",
            "notify_enitity": subs[0].__dict__,
        })

    @staticmethod
    def get_media_service_response(
            url: str,
            service_class: type[MediaService],
            high_res: bool = False
    ) -> MediaServiceResponse:
        """
        Получение результата от медиа сервиса, проставление file_id
        """

        bot = TgBot()
        event = Event()
        event.message = Message()
        if high_res:
            event.message.keys = ['high']

        logger.debug({
            "message": "get_media_result_msg",
            "notify_enitity": url,
        })
        service = service_class(bot, event)
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
    def send_notify(sub: Subscribe, title: str, url: str, media_response: MediaServiceResponse):
        logger.debug({
            "message": "send_notify",
            "notify_enitity": url,
        })
        bot = TgBot()

        if sub.playlist_title:
            answer = f"Новое видео в плейлисте {sub.playlist_title} канала {sub.channel_title}"
        else:
            answer = f"Новое видео на канале {sub.channel_title}"

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
    def _save_to_disk(media_response: MediaServiceResponse, show_name: str, series_name: str):
        logger.debug({
            "message": "_save_to_disk",
            "notify_enitity": show_name,
        })

        MediaService.save_to_disk(media_response, show_name, series_name)

        logger.debug({
            "message": "end _save_to_disk",
            "notify_enitity": show_name,
        })
