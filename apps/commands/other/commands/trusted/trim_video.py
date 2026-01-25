from datetime import datetime

from apps.bot.consts import PlatformEnum, RoleEnum
from apps.bot.core.activities import ActivitiesEnum
from apps.bot.core.bot.tg_bot.tg_bot import TgBot
from apps.bot.core.chat_activity import ChatActivity
from apps.bot.core.messages.attachments.audio import AudioAttachment
from apps.bot.core.messages.attachments.link import LinkAttachment
from apps.bot.core.messages.attachments.video import VideoAttachment
from apps.bot.core.messages.attachments.video_note import VideoNoteAttachment
from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.commands.command import Command
from apps.commands.help_text import HelpTextItem, HelpText, HelpTextArgument
from apps.connectors.parsers.media_command.youtube.video import YoutubeVideo
from apps.shared.exceptions import PWarning
from apps.shared.utils.utils import prepend_symbols, append_symbols
from apps.shared.utils.video.video_handler import VideoHandler


class TrimVideo(Command):
    name = "обрезка"
    names = ["обрежь", "обрез", "обрезание", "отрежь", "отрезание", "crop", "cut", "trim", "обрезать", "отрезать"]

    help_text = HelpText(
        commands_text="обрезание видео/аудио",
        help_texts=[
            HelpTextItem(RoleEnum.USER, [
                HelpTextArgument(
                    "(вложенное видео/аудио) (таймкод начала)",
                    "обрезает видео с таймкода и до конца"),
                HelpTextArgument(
                    "(вложенное видео/аудио) (таймкод начала) (таймкод конца)",
                    "обрезает видео по таймкодам"),
                HelpTextArgument(
                    "(youtube ссылка) (таймкод начала)",
                    "обрезает с таймкода и до конца"),
                HelpTextArgument(
                    "(youtube ссылка) (таймкод начала) (таймкод конца)",
                    "обрезает по таймкодам"),
                HelpTextArgument(
                    "(youtube ссылка с таймкодом)",
                    "обрезает с таймкода и до конца"),
                HelpTextArgument(
                    "(youtube ссылка с таймкодом) (таймкод конца)",
                    "обрезает по таймкодам"),
            ])
        ],
        extra_text=(
            "Формат для таймкодов: [%H:]%M:%S[.%MS], т.е. валидные таймкоды: 09:04, 9:04, 09:4, 9:4, 01:09:04, 9:04.123"
        )
    )

    platforms = [PlatformEnum.TG]
    bot: TgBot

    attachments = [LinkAttachment, VideoAttachment, AudioAttachment, VideoNoteAttachment]
    args = 1
    access = RoleEnum.TRUSTED

    TIMECODE_FORMAT = "%H:%M:%S.%f"

    def start(self) -> ResponseMessage:
        att = self.event.get_all_attachments(self.attachments)[0]
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_VIDEO, self.event.peer_id):
            if isinstance(att, LinkAttachment):
                if not att.is_youtube_link:
                    raise PWarning("Обрезка по ссылке доступна только для YouTube")
                video_bytes = self.trim_attachment_by_link(att)
            else:
                video_bytes = self.trim_attachment(att)

        if isinstance(att, AudioAttachment):
            attachment = self.bot.get_audio_attachment(video_bytes, peer_id=self.event.peer_id)
        else:
            attachment = self.bot.get_video_attachment(video_bytes, peer_id=self.event.peer_id)
        return ResponseMessage(ResponseMessageItem(attachments=[attachment]))

    def trim_attachment_by_link(self, att: LinkAttachment) -> bytes:
        args = [x for x in self.event.message.args]
        args.remove(att.url.lower())

        start_pos, end_pos = self.get_timecodes(att.url, args)
        return self.trim_link_pos(att.url, start_pos, end_pos)

    def trim_link_pos(self, link, start_pos, end_pos=None) -> bytes:
        delta = None
        if end_pos:
            end_dt = datetime.strptime(end_pos, self.TIMECODE_FORMAT)
            start_dt = datetime.strptime(start_pos, self.TIMECODE_FORMAT)
            delta = (end_dt - start_dt).seconds

        yt_api = YoutubeVideo()
        info = yt_api.get_video_info(link, _timedelta=delta)
        video = yt_api.download_video(info)
        return self.trim(video, start_pos, end_pos)

    def trim_attachment(self, video: VideoAttachment | AudioAttachment) -> bytes:
        start_pos = self.parse_timecode(self.event.message.args[0])
        end_pos = None
        if len(self.event.message.args) > 1:
            end_pos = self.parse_timecode(self.event.message.args[1])
        self.check_positions(start_pos, end_pos)
        return self.trim(video, start_pos, end_pos)

    @staticmethod
    def trim(video: VideoAttachment | AudioAttachment | LinkAttachment | None, start_pos: str, end_pos: str) -> bytes:
        video.download_content()
        vh = VideoHandler(video)
        return vh.trim(start_pos, end_pos)

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
    def get_timecodes(cls, url: str, args: list) -> tuple[str | None, str | None]:
        """
        Метод вытаскивает таймкоды для команды Trim
        """
        yt_api = YoutubeVideo()
        start_yt_timecode = yt_api.get_timecode_str(url)

        end_pos = None
        if start_yt_timecode:
            start_pos = TrimVideo.parse_timecode(start_yt_timecode)
            if args:
                try:
                    end_pos = TrimVideo.parse_timecode(args[0])
                except ValueError:
                    end_pos = None
        elif args:
            try:
                start_pos = TrimVideo.parse_timecode(args[0])
                if len(args) > 1:
                    try:
                        end_pos = TrimVideo.parse_timecode(args[1])
                    except ValueError:
                        end_pos = None
            except ValueError:
                return None, None
        else:
            return None, None
        cls.check_positions(start_pos, end_pos)
        return start_pos, end_pos

    @classmethod
    def check_positions(cls, start_pos, end_pos):
        if start_pos and end_pos and \
                datetime.strptime(start_pos, cls.TIMECODE_FORMAT) > datetime.strptime(end_pos, cls.TIMECODE_FORMAT):
            raise PWarning("Первый таймкод больше второго")
