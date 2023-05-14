from datetime import datetime

from apps.bot.APIs.YoutubeVideoAPI import YoutubeVideoAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.classes.messages.attachments.LinkAttachment import LinkAttachment
from apps.bot.classes.messages.attachments.VideoAttachment import VideoAttachment
from apps.bot.utils.VideoTrimmer import VideoTrimmer


class TrimVideo(Command):
    name = "обрезка"
    names = ["обрежь", "обрез", "обрезание", "отрежь", "отрезание", "crop", "cut", "trim"]
    name_tg = "trim"

    help_text = "обрезание видео"
    help_texts = [
        "(вложенное видео) (таймкод начала) (таймкод конца) - обрезает видео по таймкодам",
        "(youtube ссылка) (таймкод начала) - обрезает с таймкода и до конца",
        "(youtube ссылка) (таймкод начала) (таймкод конца) - обрезает по таймкодам",
        "(youtube ссылка с таймкодом) - обрезает с таймкода и до конца",
        "(youtube ссылка с таймкодом) (таймкод конца) - обрезает по таймкодам",
    ]
    help_texts_extra = "Формат для таймкодов: %M:%S, т.е. валидные таймкоды: 09:04, 9:04, 09:4, 9:4"
    platforms = [Platform.TG]
    bot: TgBot

    attachments = [LinkAttachment, VideoAttachment]
    args = 1

    def start(self):
        att = self.event.get_all_attachments([LinkAttachment, VideoAttachment])[0]
        if isinstance(att, LinkAttachment):
            if not att.is_youtube_link:
                raise PWarning("Обрезка по ссылке доступна только для YouTube")
            video_bytes = self.parse_link(att)
        else:
            video_bytes = self.parse_video(att)
        video = self.bot.get_video_attachment(video_bytes, peer_id=self.event.peer_id)
        return {'attachments': [video]}

    def parse_link(self, att, args=None, platform=None):
        yt_api = YoutubeVideoAPI()

        if args is None:
            args = [x for x in self.event.message.args]
            args.remove(att.url.lower())

        delta = None
        end_pos = None
        yt_timecode = yt_api.get_timecode_str(att.url)
        if yt_timecode:
            start_pos = yt_timecode
            if args:
                end_pos = args[0]
        else:
            if not args:
                raise PWarning("Должны быть переданы аргументы или таймкод должен быть в ссылке youtube видео")
            start_pos = args[0]
            if len(args) == 2:
                end_pos = args[1]

        if end_pos:
            delta = (datetime.strptime(end_pos, "%M:%S") - datetime.strptime(start_pos, "%M:%S")).seconds
        start_pos = self.parse_timecode(start_pos)
        end_pos = self.parse_timecode(end_pos)

        platform = self.event.platform if self.event else platform
        download_url = yt_api.get_video_download_url(att.url, platform, timedelta=delta)
        vt = VideoTrimmer()
        return vt.trim(download_url, start_pos, end_pos)

    def parse_video(self, video: VideoAttachment):
        start_pos = self.parse_timecode(self.event.message.args[0])
        end_pos = self.parse_timecode(self.event.message.args[1])

        vt = VideoTrimmer()
        return vt.trim(video.private_download_url, start_pos, end_pos)

    def parse_timecode(self, timecode):
        dt = datetime.strptime(timecode, "%M:%S")
        return dt.strftime("%H:%M:%S")
