from urllib.parse import urlparse

import requests
import youtube_dl

from apps.bot.classes.Consts import Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand

YOUTUBE_URLS = ['www.youtube.com', 'youtube.com', "www.youtu.be", "youtu.be"]


class Media(CommonCommand):
    name = "медиа"
    help_text = "скачивает видео из Reddit/TikTok/YouTube и присылает его"
    help_texts = [
        "(ссылка на видео) - скачивает видео из Reddit/TikTok/YouTube и присылает его"
    ]
    platforms = [Platform.TG]

    def accept(self, event):
        if urlparse(event.command).hostname in YOUTUBE_URLS:
            return True
        if event.fwd:
            if urlparse(event.fwd[0]['text']).hostname in YOUTUBE_URLS:
                return True
        return super().accept(event)

    def start(self):
        self.bot.set_activity(self.event.peer_id, 'upload_video')

        if self.event.command in self.full_names:
            if self.event.args:
                url = self.event.args[0]
            elif self.event.fwd:
                url = self.event.fwd[0]['text']
            else:
                raise PWarning("Для работы команды требуются аргументы или пересылаемые сообщения")
        else:
            url = self.event.clear_msg

        if urlparse(url).hostname not in YOUTUBE_URLS:
            raise PWarning("Не youtube ссылка")

        if self.event.command not in self.full_names:
            try:
                video, title = self.get_youtube_video_info(url)
                self.bot.delete_message(self.event.peer_id, self.event.msg_id)
                attachments = [self.bot.upload_video(video)]
                msg = f"{title}\n" \
                      f"От пользователя {self.event.sender}\n" \
                      f"{url}"
                return {'msg': msg, 'attachments': attachments}
            except Exception:
                return
        else:
            video, _ = self.get_youtube_video_info(url)
            attachments = [self.bot.upload_video(video)]
            return {
                'attachments': attachments
            }

    def get_youtube_video_info(self, url):
        ydl_params = {
            'outtmpl': '%(id)s%(ext)s',
            'logger': NothingLogger()
        }
        ydl = youtube_dl.YoutubeDL(ydl_params)
        ydl.add_default_info_extractors()

        try:
            video_info = ydl.extract_info(url, download=False)
        except youtube_dl.utils.DownloadError:
            raise PWarning("Не смог найти видео по этой ссылке")
        video_urls = []
        if video_info['duration'] > 60:
            raise PWarning("Нельзя грузить видосы > 60 секунд с ютуба")
        if 'formats' in video_info:
            for _format in video_info['formats']:
                if _format['ext'] == 'mp4' and _format['asr']:
                    video_urls.append(_format)

        if len(video_urls) == 0:
            raise PWarning("Чёт проблемки, напишите разрабу и пришли ссылку на видео")
        max_quality_video = sorted(video_urls, key=lambda x: x['format_note'])[0]
        url = max_quality_video['url']
        video_content = requests.get(url).content
        return video_content, video_info['title']


class NothingLogger(object):
    @staticmethod
    def debug(msg):
        pass

    @staticmethod
    def warning(msg):
        pass

    @staticmethod
    def error(msg):
        print(msg)
