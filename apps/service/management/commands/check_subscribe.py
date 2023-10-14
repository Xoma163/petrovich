import logging
import os
import shutil
import time
from itertools import groupby

from django.core.management import BaseCommand

from apps.bot.api.premier import Premier
from apps.bot.api.thehole import TheHole
from apps.bot.api.vk.video import VKVideo
from apps.bot.api.youtube.video import YoutubeVideo
from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.event.event import Event
from apps.bot.classes.messages.message import Message
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.commands.trusted.media import Media
from apps.service.models import Subscribe, VideoCache
from petrovich.settings import env

logger = logging.getLogger('subscribe_notifier')


class Command(BaseCommand):
    SERVICE_CLASS = {
        Subscribe.SERVICE_YOUTUBE: YoutubeVideo,
        Subscribe.SERVICE_THE_HOLE: TheHole,
        Subscribe.SERVICE_VK: VKVideo,
        Subscribe.SERVICE_PREMIERE: Premier
    }
    SERVICE_MEDIA_METHOD = {
        Subscribe.SERVICE_YOUTUBE: "get_youtube_video",
        Subscribe.SERVICE_THE_HOLE: "get_the_hole_video",
        Subscribe.SERVICE_VK: "get_vk_video",
        Subscribe.SERVICE_PREMIERE: "get_premiere_video"
    }

    def handle(self, *args, **kwargs):
        subs = Subscribe.objects.all()
        groupped_subs = groupby(subs.order_by("channel_id"), lambda x: (x.service, x.channel_id, x.playlist_id))

        for (service, _, _), subs in groupped_subs:
            sub_class = self.SERVICE_CLASS[service]
            media_method = self.SERVICE_MEDIA_METHOD[service]
            subs = list(subs)
            try:
                self.check_video(subs, sub_class, media_method)
            except PWarning:
                pass
            except Exception:
                logger.exception({"message": "Ошибка в проверке/отправке подписки", "notify_enitity": subs[0].__dict__})

    def check_video(self, subs, sub_class, media_method):
        if len(set(x.last_video_id for x in subs)) == 1:
            api = sub_class()
            res = api.get_filtered_new_videos(subs[0].channel_id, subs[0].last_video_id,
                                              playlist_id=subs[0].playlist_id)
            if not res['ids']:
                return

            self.send_file_or_video(subs, res["ids"], res["urls"], res["titles"], method=media_method)
        else:
            for sub in subs:
                self.check_video([sub], sub_class, media_method)

    @staticmethod
    def send_notify(sub, title, link, media_message: ResponseMessageItem):
        bot = TgBot()

        if sub.playlist_id:
            answer = f"Новое видео в плейлисте {sub.title}"
        else:
            answer = f"Новое видео на канале {sub.title}"

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

    @staticmethod
    def get_media_result_msg(link, method) -> ResponseMessageItem:
        bot = TgBot()
        event = Event(bot=bot)
        event.message = Message()
        media_command = Media(bot, event)
        media_command.has_command_name = True
        att, title = getattr(media_command, method)(link)
        rmi = ResponseMessageItem(text=title, attachments=att)
        return rmi

    def send_file_or_video(self, subs, ids, urls, titles, method):
        rm = ResponseMessage()
        for i, url in enumerate(urls):
            media_message = self.get_media_result_msg(url, method)
            if media_message.attachments:
                att = media_message.attachments[0]
                if not att.file_id:
                    att.set_file_id()
            rm.messages.append(media_message)

        for sub in subs:
            for i, media_message in enumerate(rm.messages):
                self.send_notify(sub, titles[i], urls[i], media_message)

                if sub.save_to_plex:
                    cache = VideoCache.objects.get(channel_id=sub.channel_id, video_id=ids[i])
                    self._save_to_plex(cache, sub.title, titles[i])

                time.sleep(1)
            sub.last_video_id = ids[-1]
            sub.save()

    @staticmethod
    def _save_to_plex(cache, show_name, series_name):
        path = env.str('PLEX_SAVE_PATH')
        show_name = show_name.replace(" |", '.').replace("|", ".")
        series_name = series_name.replace(" |", '.').replace("|", ".")

        show_folder = os.path.join(path, show_name)
        if not os.path.exists(show_folder):
            os.makedirs(show_folder)
        shutil.copyfile(cache.video.path, os.path.join(str(show_folder), f"{series_name}.mp4"))
