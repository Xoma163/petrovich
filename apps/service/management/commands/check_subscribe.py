import logging
import os
import shutil
import time
from itertools import groupby

from django.core.management import BaseCommand

from apps.bot.api.premier import Premier
from apps.bot.api.subscribe_service import SubscribeServiceNewVideosData
from apps.bot.api.vk.video import VKVideo
from apps.bot.api.youtube.video import YoutubeVideo
from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.const.exceptions import PSubscribeIndexError
from apps.bot.classes.event.event import Event
from apps.bot.classes.messages.message import Message
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.bot.commands.media import Media
from apps.service.models import Subscribe, VideoCache
from petrovich.settings import env

logger = logging.getLogger('subscribe_notifier')


class Command(BaseCommand):
    SERVICE_CLASS = {
        Subscribe.SERVICE_YOUTUBE: YoutubeVideo,
        Subscribe.SERVICE_VK: VKVideo,
        Subscribe.SERVICE_PREMIERE: Premier
    }
    SERVICE_MEDIA_METHOD = {
        Subscribe.SERVICE_YOUTUBE: "get_youtube_video",
        Subscribe.SERVICE_VK: "get_vk_video",
        Subscribe.SERVICE_PREMIERE: "get_premiere_video"
    }

    def handle(self, *args, **kwargs):
        logger.debug({
            "message": "handle"
        })
        subs = Subscribe.objects.all()
        groupped_subs = groupby(subs.order_by("channel_id"), lambda x: (x.service, x.channel_id, x.playlist_id))

        for (service, _, _), subs in groupped_subs:
            sub_class = self.SERVICE_CLASS[service]
            media_method = self.SERVICE_MEDIA_METHOD[service]
            subs = list(subs)
            try:
                self.check_video(subs, sub_class, media_method)
            except Exception:
                logger.exception({
                    "message": "Ошибка в проверке/отправке подписки",
                    "notify_enitity": subs[0].__dict__,
                })
        logger.debug({
            "message": "end handle"
        })

    def check_video(self, subs, sub_class, media_method):
        if len(set(x.last_videos_id[-1] for x in subs)) == 1:
            api = sub_class()
            try:
                res = api.get_filtered_new_videos(
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

            if not res.videos:
                return

            self.send_file_or_video(subs, res, method=media_method)
        else:
            for sub in subs:
                self.check_video([sub], sub_class, media_method)

    @staticmethod
    def send_notify(sub, title, link, media_message: ResponseMessageItem):
        logger.debug({
            "message": "send_notify",
            "notify_enitity": link,
        })
        bot = TgBot()

        if sub.playlist_title:
            answer = f"Новое видео в плейлисте {sub.playlist_title} канала {sub.channel_title}"
        else:
            answer = f"Новое видео на канале {sub.channel_title}"

        answer += f"\n\n{media_message.text}"
        answer = answer.replace(title, bot.get_formatted_url(title, link))
        rmi = ResponseMessageItem(
            text=answer,
            peer_id=sub.peer_id,
            message_thread_id=sub.message_thread_id,
            attachments=media_message.attachments
        )
        bot.send_response_message_item(rmi)
        logger.info(f"Отправил уведомление по подписке с id={sub.pk}")
        logger.debug({
            "message": "end send_notify",
            "notify_enitity": link,
        })

    @staticmethod
    def get_media_result_msg(link, method) -> ResponseMessageItem:
        logger.debug({
            "message": "get_media_result_msg",
            "notify_enitity": link,
        })
        bot = TgBot()
        event = Event()
        event.message = Message()
        media_command = Media(bot, event)
        media_command.has_command_name = True
        att, title = getattr(media_command, method)(link)
        rmi = ResponseMessageItem(text=title, attachments=att)
        logger.debug({
            "message": "end get_media_result_msg",
            "notify_enitity": link,
        })
        return rmi

    def send_file_or_video(self, subs, videos: SubscribeServiceNewVideosData, method):
        logger.debug({
            "message": "send_file_or_video",
            "notify_enitity": subs[0].__dict__,
        })
        messages_with_att = []
        for video in videos.videos:
            media_message: ResponseMessageItem = self.get_media_result_msg(video.url, method)
            if media_message.attachments:
                att = media_message.attachments[0]
                if not att.file_id:
                    att.set_file_id()
            messages_with_att.append((media_message, video))

        for sub in subs:
            for rmi, video in messages_with_att:
                self.send_notify(sub, video.title, video.url, rmi)

                if sub.save_to_plex:
                    cache = VideoCache.objects.get(channel_id=sub.channel_id, video_id=video.id)
                    self._save_to_plex(cache, str(sub), video.title)

                time.sleep(1)
            sub.last_videos_id = sub.last_videos_id + videos.ids
            sub.save()

        logger.debug({
            "message": "end send_file_or_video",
            "notify_enitity": subs[0].__dict__,
        })

    @staticmethod
    def _save_to_plex(cache, show_name, series_name):
        logger.debug({
            "message": "_save_to_plex",
            "notify_enitity": show_name,
        })

        path = env.str('PLEX_SAVE_PATH')
        show_name = show_name.replace(" |", '.').replace("|", ".")
        series_name = series_name.replace(" |", '.').replace("|", ".")

        show_folder = os.path.join(path, show_name)
        if not os.path.exists(show_folder):
            os.makedirs(show_folder)
        shutil.copyfile(cache.video.path, os.path.join(str(show_folder), f"{series_name}.mp4"))

        logger.debug({
            "message": "end _save_to_plex",
            "notify_enitity": show_name,
        })
