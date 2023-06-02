import logging
import time
from itertools import groupby

from django.core.management import BaseCommand

from apps.bot.APIs.TheHoleAPI import TheHoleAPI
from apps.bot.APIs.VKVideoAPI import VKVideoAPI
from apps.bot.APIs.WASDAPI import WASDAPI
from apps.bot.APIs.YoutubeVideoAPI import YoutubeVideoAPI
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.events.Event import Event
from apps.bot.commands.Media import Media
from apps.bot.models import Chat
from apps.service.models import Subscribe
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
            try:
                self.check_subs(service, subs)
            except Exception:
                logger.exception("Ошибка в проверке/отправке оповещения о стриме")

    def check_subs(self, service, subs):
        # if service == Subscribe.SERVICE_YOUTUBE:
        #     self.check_youtube_video(subs)
        if service == Subscribe.SERVICE_THE_HOLE:
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
                sub.save()
                return
            title = youtube_data['last_video']['title']
            link = youtube_data['last_video']['link']
            self.send_notify(sub, title, link)

            sub.date = youtube_data['last_video']['date']
            sub.save()
            time.sleep(2)

    def check_the_hole_video(self, subs):
        if len(set(x.last_video_id for x in subs)) == 1:
            th_api = TheHoleAPI()
            ids, titles = th_api.get_last_videos_with_titles(subs[0].channel_id, subs[0].last_video_id)
            if len(ids) == 0:
                return

            urls = [f"{th_api.URL}{link}" for link in ids]
            self.send_file_or_video(subs, ids, urls, titles, method=self.get_the_hole_video_msg, _type='document')
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
            ids, titles = vk_v_api.get_last_video_ids_with_titles(subs[0].channel_id, subs[0].last_video_id)
            if len(ids) == 0:
                return

            urls = [f"{vk_v_api.URL}{x}" for x in ids]
            self.send_file_or_video(subs, ids, urls, titles, method=self.get_vk_video_msg, _type='video')
        else:
            for sub in subs:
                self.check_vk_video([sub])

    @staticmethod
    def send_notify(sub, title, link, is_stream=False):
        bot = TgBot()

        new_video_text = "Новое видео" if not is_stream else "Стрим"

        text = f"{new_video_text} на канале {sub.title}\n" \
               f"{bot.get_formatted_url(title, link)}"
        logger.info(f"Отправил уведомление по подписке с id={sub.pk}")
        bot.parse_and_send_msgs(text, sub.peer_id, sub.message_thread_id)

    @staticmethod
    def get_the_hole_video_msg(link):
        bot = TgBot()
        event = Event(bot=bot)
        media_command = Media(bot, event)
        att, title = media_command.get_the_hole_video(link)
        msg = {'text': title, 'attachments': att}
        return msg

    @staticmethod
    def get_vk_video_msg(link):
        bot = TgBot()
        event = Event(bot=bot)
        media_command = Media(bot, event)
        att, title = media_command.get_vk_video(link)
        msg = {'text': title, 'attachments': att}
        return msg

    def send_file_or_video(self, subs, ids, urls, titles, method, _type):
        bot = TgBot()
        video_uploading_chat = Chat.objects.get(pk=env.str("TG_PHOTO_UPLOADING_CHAT_PK"))
        messages = []
        for i, url in enumerate(urls):
            message = method(url)

            r = bot.parse_and_send_msgs(message, video_uploading_chat.chat_id)
            r_json = r[0]['response'].json()
            bot.delete_message(video_uploading_chat.chat_id, r_json['result']['message_id'])
            file_id = r_json['result'][_type]['file_id']

            message['attachments'][0].file_id = file_id
            messages.append(message)

        for sub in subs:
            for i, message in enumerate(messages):
                self.send_notify(sub, titles[i], urls[i])
                bot.parse_and_send_msgs(message, sub.peer_id, sub.message_thread_id)
            sub.last_video_id = ids[-1]
            sub.save()
