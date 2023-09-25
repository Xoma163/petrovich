import logging
import os
import shutil
import time
from itertools import groupby

from django.core.management import BaseCommand

from apps.bot.APIs.PremiereAPI import PremiereAPI
from apps.bot.APIs.TheHoleAPI import TheHoleAPI
from apps.bot.APIs.VKVideoAPI import VKVideoAPI
from apps.bot.APIs.YoutubeVideoAPI import YoutubeVideoAPI
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.events.Event import Event
from apps.bot.classes.messages.Message import Message
from apps.bot.classes.messages.ResponseMessage import ResponseMessageItem, ResponseMessage
from apps.bot.commands.TrustedCommands.Media import Media
from apps.service.models import Subscribe, VideoCache
from petrovich.settings import env

logger = logging.getLogger('subscribe_notifier')


class Command(BaseCommand):

    def __init__(self):
        super().__init__()

    def handle(self, *args, **kwargs):
        subs = Subscribe.objects.all()
        groupped_subs = groupby(subs.order_by("channel_id"), lambda x: (x.service, x.channel_id, x.playlist_id))
        for (service, _), subs in groupped_subs:
            service_class = {
                Subscribe.SERVICE_YOUTUBE: YoutubeVideoAPI,
                Subscribe.SERVICE_THE_HOLE: TheHoleAPI,
                Subscribe.SERVICE_VK: VKVideoAPI,
                Subscribe.SERVICE_PREMIERE: PremiereAPI
            }
            service_media_method = {
                Subscribe.SERVICE_YOUTUBE: "get_youtube_video",
                Subscribe.SERVICE_THE_HOLE: "get_the_hole_video",
                Subscribe.SERVICE_VK: "get_vk_video",
                Subscribe.SERVICE_PREMIERE: "get_premiere_video"
            }
            sub_class = service_class[service]
            media_method = service_media_method[service]
            self.check_video(list(subs), sub_class, media_method)

    def check_video(self, subs, sub_class, media_method):
        if len(set(x.last_video_id for x in subs)) == 1:
            yt_api = sub_class()
            res = yt_api.get_filtered_new_videos(subs[0].channel_id, subs[0].last_video_id,
                                                 playlist_id=subs[0].playlist_id)
            if not res['ids']:
                return

            self.send_file_or_video(subs, res["ids"], res["urls"], res["titles"], method=media_method)
        else:
            for sub in subs:
                self.check_video([sub], sub_class, media_method)

    @staticmethod
    def send_notify(sub, title, link):
        bot = TgBot()

        answer = f"Новое видео на канале {sub.title}\n" \
                 f"{bot.get_formatted_url(title, link)}"
        logger.info(f"Отправил уведомление по подписке с id={sub.pk}")
        rmi = ResponseMessageItem(text=answer, peer_id=sub.peer_id, message_thread_id=sub.message_thread_id)
        bot.send_response_message_item(rmi)

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
        bot = TgBot()
        rm = ResponseMessage()
        for i, url in enumerate(urls):
            message = self.get_media_result_msg(url, method)
            if message.attachments:
                att = message.attachments[0]
                if not att.file_id:
                    att.set_file_id()
            rm.messages.append(message)

        for sub in subs:
            for i, message in enumerate(rm.messages):
                self.send_notify(sub, titles[i], urls[i])
                message.peer_id = sub.peer_id
                message.message_thread_id = sub.message_thread_id
                bot.send_response_message_item(message)

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
        shutil.copyfile(cache.video.path, os.path.join(show_folder, f"{series_name}.mp4"))
