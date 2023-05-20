from datetime import datetime

from apps.bot.APIs.YoutubeVideoAPI import YoutubeVideoAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum
from apps.bot.classes.consts.Consts import Platform, Role
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.classes.messages.attachments.LinkAttachment import LinkAttachment
from apps.bot.classes.messages.attachments.VideoAttachment import VideoAttachment
from apps.bot.utils.VideoTrimmer import VideoTrimmer
from apps.bot.utils.utils import prepend_symbols, append_symbols


class TrimVideo(Command):
    name = "обрезка"
    names = ["обрежь", "обрез", "обрезание", "отрежь", "отрезание", "crop", "cut", "trim", "обрезать", "отрезать"]
    name_tg = "trim"

    help_text = "обрезание видео"
    help_texts = [
        "(вложенное видео) (таймкод начала) - обрезает видео с таймкода и до конца",
        "(вложенное видео) (таймкод начала) (таймкод конца) - обрезает видео по таймкодам",
        "(youtube ссылка) (таймкод начала) - обрезает с таймкода и до конца",
        "(youtube ссылка) (таймкод начала) (таймкод конца) - обрезает по таймкодам",
        "(youtube ссылка с таймкодом) - обрезает с таймкода и до конца",
        "(youtube ссылка с таймкодом) (таймкод конца) - обрезает по таймкодам",
    ]
    help_texts_extra = "Формат для таймкодов: [%H:]%M:%S[.%MS], т.е. валидные таймкоды: 09:04, 9:04, 09:4, 9:4, 01:09:04, 9:04.123"
    platforms = [Platform.TG]
    bot: TgBot

    attachments = [LinkAttachment, VideoAttachment]
    args = 1

    def start(self):
        att = self.event.get_all_attachments([LinkAttachment, VideoAttachment])[0]
        try:
            self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.UPLOAD_VIDEO)
            if isinstance(att, LinkAttachment):
                if not att.is_youtube_link:
                    raise PWarning("Обрезка по ссылке доступна только для YouTube")
                video_bytes = self.parse_link(att)
            else:
                video_bytes = self.parse_video(att)
        finally:
            self.bot.stop_activity_thread()

        video = self.bot.get_video_attachment(video_bytes, peer_id=self.event.peer_id)
        return {'attachments': [video]}

    def parse_link(self, att):
        yt_api = YoutubeVideoAPI()

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

        start_pos = self.parse_timecode(start_pos)
        if end_pos:
            end_pos = self.parse_timecode(end_pos)
            delta = (datetime.strptime(end_pos, "%H:%M:%S.%f") - datetime.strptime(start_pos, "%H:%M:%S.%f")).seconds

        download_url = yt_api.get_video_download_url(att.url, self.event.platform, timedelta=delta)
        if yt_api.filesize > 100 and not self.event.sender.check_role(Role.TRUSTED):
            raise PWarning("Нельзя грузить отрезки из ютуба больше 100мб")
        return self.trim(download_url, start_pos, end_pos)

    def parse_video(self, video: VideoAttachment):
        start_pos = self.parse_timecode(self.event.message.args[0])
        end_pos = None
        if len(self.event.message.args) > 1:
            end_pos = self.parse_timecode(self.event.message.args[1])
        video = video.download_content(self.event.peer_id)
        return self.trim(video, start_pos, end_pos)

    @staticmethod
    def trim(video, start_pos, end_pos):
        vt = VideoTrimmer()
        return vt.trim(video, start_pos, end_pos)

    @classmethod
    def parse_timecode(cls, timecode):
        h = "0"
        m = "0"
        s = "0"
        ms = "0"
        numbers = []
        last_save_index = 0

        dot_in_timecode = False
        for i, symbol in enumerate(timecode):
            if symbol == ":":
                numbers.append(timecode[last_save_index:i])
                last_save_index = i + 1
            if symbol == ".":
                dot_in_timecode = True
                numbers.append(timecode[last_save_index:i])
                ms = timecode[i + 1:len(timecode)]
                break
        if not dot_in_timecode:
            numbers.append(timecode[last_save_index:len(timecode)])
        if len(numbers) == 3:
            h, m, s = numbers
        elif len(numbers) == 2:
            m, s = numbers
        elif len(numbers) == 1:
            s = numbers[0]
        else:
            raise PWarning("Ошибка парсинга таймкода")
        res = f"{prepend_symbols(h, '0', 2)}:{prepend_symbols(m, '0', 2)}:{prepend_symbols(s, '0', 2)}.{append_symbols(ms, '0', 3)}"
        return res
