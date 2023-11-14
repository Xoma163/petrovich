from datetime import datetime
from typing import Tuple, Optional

from apps.bot.api.youtube.video import YoutubeVideo
from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Platform, Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.attachments.link import LinkAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import prepend_symbols, append_symbols
from apps.bot.utils.video.trimmer import VideoTrimmer


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

    def start(self) -> ResponseMessage:
        att = self.event.get_all_attachments([LinkAttachment, VideoAttachment])[0]
        try:
            self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.UPLOAD_VIDEO)
            if isinstance(att, LinkAttachment):
                if not att.is_youtube_link:
                    raise PWarning("Обрезка по ссылке доступна только для YouTube")
                video_bytes = self.trim_att_by_link(att)
            else:
                video_bytes = self.trim_video(att)
        finally:
            self.bot.stop_activity_thread()

        video = self.bot.get_video_attachment(video_bytes, peer_id=self.event.peer_id)
        return ResponseMessage(ResponseMessageItem(attachments=[video]))

    def trim_att_by_link(self, att) -> bytes:
        args = [x for x in self.event.message.args]
        args.remove(att.url.lower())

        start_pos, end_pos = self.get_timecodes(att.url, args)
        return self.trim_link_pos(att.url, start_pos, end_pos)

    def trim_link_pos(self, link, start_pos, end_pos=None) -> bytes:
        delta = None
        if end_pos:
            delta = (datetime.strptime(end_pos, "%H:%M:%S.%f") - datetime.strptime(start_pos, "%H:%M:%S.%f")).seconds
        max_filesize_mb = self.bot.MAX_VIDEO_SIZE_MB if isinstance(self.bot, TgBot) else None
        yt_api = YoutubeVideo()
        data = yt_api.get_video_info(link, _timedelta=delta, max_filesize_mb=max_filesize_mb)
        if data['filesize'] > 100 and not self.event.sender.check_role(Role.TRUSTED):
            raise PWarning("Нельзя грузить отрезки из ютуба больше 100мб")
        return self.trim(data['download_url'], start_pos, end_pos)

    def trim_video(self, video: VideoAttachment) -> bytes:
        start_pos = self.parse_timecode(self.event.message.args[0])
        end_pos = None
        if len(self.event.message.args) > 1:
            end_pos = self.parse_timecode(self.event.message.args[1])
        video = video.download_content(self.event.peer_id)
        return self.trim(video, start_pos, end_pos)

    @staticmethod
    def trim(video, start_pos: str, end_pos: str) -> bytes:
        vt = VideoTrimmer()
        return vt.trim(video, start_pos, end_pos)

    @classmethod
    def parse_timecode(cls, timecode: str) -> str:
        h = 0
        m = 0
        ms = 0
        numbers = []
        last_save_index = 0

        dot_in_timecode = False
        for i, symbol in enumerate(timecode):
            if symbol == ":":
                numbers.append(int(timecode[last_save_index:i]))
                last_save_index = i + 1
            if symbol == ".":
                dot_in_timecode = True
                numbers.append(int(timecode[last_save_index:i]))

                ms = timecode[i + 1:len(timecode)]
                break
        if not dot_in_timecode:
            n = int(timecode[last_save_index:len(timecode)])
            numbers.append(n)
        if len(numbers) == 3:
            h, m, s = numbers
        elif len(numbers) == 2:
            m, s = numbers
        elif len(numbers) == 1:
            s = numbers[0]
        else:
            raise PWarning("Ошибка парсинга таймкода")

        s_div_60 = s // 60
        if s_div_60 > 0:
            s = s % 60
            m += s_div_60

        m_div_60 = m // 60
        if m_div_60 > 0:
            m = m % 60
            h += m_div_60

        res = f"{prepend_symbols(str(h), '0', 2)}:{prepend_symbols(str(m), '0', 2)}:" \
              f"{prepend_symbols(str(s), '0', 2)}.{append_symbols(str(ms), '0', 3)}"
        return res

    @classmethod
    def get_timecodes(cls, url: str, args: list) -> Tuple[Optional[str], Optional[str]]:
        """
        Метод вытаскивает таймкоды для команды Trim
        """
        yt_api = YoutubeVideo()
        start_yt_timecode = yt_api.get_timecode_str(url)

        end_pos = None
        if start_yt_timecode:
            start_pos = TrimVideo.parse_timecode(start_yt_timecode)
            if args:
                end_pos = TrimVideo.parse_timecode(args[0])
        elif args:
            try:
                start_pos = TrimVideo.parse_timecode(args[0])
                if len(args) > 1:
                    end_pos = TrimVideo.parse_timecode(args[1])
            except ValueError:
                return None, None
        else:
            return None, None
        return start_pos, end_pos
