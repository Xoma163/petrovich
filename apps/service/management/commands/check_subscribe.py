import logging
import os
import shutil
import time
from itertools import groupby

from django.core.management import BaseCommand

from apps.bot.APIs.TheHoleAPI import TheHoleAPI
from apps.bot.APIs.VKVideoAPI import VKVideoAPI
from apps.bot.APIs.WASDAPI import WASDAPI
from apps.bot.APIs.YoutubeVideoAPI import YoutubeVideoAPI
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.events.Event import Event
from apps.bot.classes.messages.ResponseMessage import ResponseMessageItem, ResponseMessage
from apps.bot.commands.Media import Media
from apps.service.models import Subscribe, VideoCache
from petrovich.settings import env

logger = logging.getLogger('subscribe_notifier')


class Command(BaseCommand):

    def __init__(self):
        super().__init__()

    def handle(self, *args, **kwargs):
        subs = Subscribe.objects.all()
        groupped_subs = groupby(subs.order_by("channel_id"), lambda x: (x.service, x.channel_id))
        for (service, _), subs in groupped_subs:
            subs = list(subs)
            # try:
            self.check_subs(service, subs)
            # except Exception:
            #     logger.exception("Ошибка в проверке/отправке оповещения о стриме")

    def check_subs(self, service, subs):
        if service == Subscribe.SERVICE_YOUTUBE:
            self.check_youtube_video(subs)
        elif service == Subscribe.SERVICE_THE_HOLE:
            self.check_the_hole_video(subs)
        elif service == Subscribe.SERVICE_WASD:
            self.check_wasd_video(subs)
        elif service == Subscribe.SERVICE_VK:
            self.check_vk_video(subs)

    def check_youtube_video(self, subs):
        for sub in subs:
            youtube_info = YoutubeVideoAPI()
            youtube_data = youtube_info.get_last_video(sub.channel_id)
            if not youtube_data['last_video']['date'] > sub.date:
                return
            is_shorts = youtube_data['last_video']['is_shorts']
            if sub.youtube_ignore_shorts and is_shorts:
                sub.date = youtube_data['last_video']['date']
                sub.last_video_id = youtube_data['last_video']['id']  # прост так.
                sub.save()
                return
            title = youtube_data['last_video']['title']
            link = youtube_data['last_video']['link']
            self.send_notify(sub, title, link)

            sub.date = youtube_data['last_video']['date']
            sub.save()
            time.sleep(1)

    def check_the_hole_video(self, subs):
        if len(set(x.last_video_id for x in subs)) == 1:
            th_api = TheHoleAPI()
            ids, titles = th_api.get_last_videos_with_titles(subs[0].channel_id, subs[0].last_video_id)
            if len(ids) == 0:
                return

            urls = [f"{th_api.URL}{link}" for link in ids]
            self.send_file_or_video(subs, ids, urls, titles, method=self.get_the_hole_video_msg)
        else:
            for sub in subs:
                self.check_the_hole_video([sub])

    def check_wasd_video(self, subs):
        for sub in subs:
            wasd = WASDAPI()
            channel_is_live = wasd.channel_is_live(sub.title)
            if not channel_is_live or sub.last_stream_status:
                sub.last_stream_status = channel_is_live
                sub.save()
                return

            link = f"{wasd.URL}{sub.title}"
            self.send_notify(sub, wasd.title, link, is_stream=True)

            sub.last_stream_status = channel_is_live
            sub.save()

    def check_vk_video(self, subs):
        if len(set(x.last_video_id for x in subs)) == 1:
            vk_v_api = VKVideoAPI()
            ids, titles = vk_v_api.get_last_video_ids_with_titles(subs[0].playlist_id or subs[0].channel_id,
                                                                  subs[0].last_video_id)
            if len(ids) == 0:
                return

            urls = [f"{vk_v_api.URL}{x}" for x in ids]
            self.send_file_or_video(subs, ids, urls, titles, method=self.get_vk_video_msg)
        else:
            for sub in subs:
                self.check_vk_video([sub])

    @staticmethod
    def send_notify(sub, title, link, is_stream=False):
        bot = TgBot()

        new_video_text = "Новое видео" if not is_stream else "Стрим"

        answer = f"{new_video_text} на канале {sub.title}\n" \
                 f"{bot.get_formatted_url(title, link)}"
        logger.info(f"Отправил уведомление по подписке с id={sub.pk}")
        rmi = ResponseMessageItem(text=answer, peer_id=sub.peer_id, message_thread_id=sub.message_thread_id)
        bot.send_response_message_item(rmi)

    @staticmethod
    def get_the_hole_video_msg(link) -> ResponseMessageItem:
        bot = TgBot()
        event = Event(bot=bot)
        media_command = Media(bot, event)
        att, title = media_command.get_the_hole_video(link)
        rmi = ResponseMessageItem(text=title, attachments=att)
        return rmi

    @staticmethod
    def get_vk_video_msg(link) -> ResponseMessageItem:
        bot = TgBot()
        event = Event(bot=bot)
        media_command = Media(bot, event)
        att, title = media_command.get_vk_video(link)
        rmi = ResponseMessageItem(text=title, attachments=att)
        return rmi

    def send_file_or_video(self, subs, ids, urls, titles, method):
        bot = TgBot()
        rm = ResponseMessage()
        for i, url in enumerate(urls):
            message = method(url)
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
