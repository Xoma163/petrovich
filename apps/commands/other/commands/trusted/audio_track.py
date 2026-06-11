from apps.bot.consts import RoleEnum
from apps.bot.core.messages.attachments.video import VideoAttachment
from apps.bot.core.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.commands.command import Command
from apps.commands.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.shared.utils.utils import prepare_filename
from apps.shared.utils.video.video_handler import VideoHandler


# ToDo: mp3
class AudioTrack(Command):
    name = "аудиодорожка"
    names = ["аудио"]

    help_text = HelpText(
        commands_text="Вырезает аудиодорожку из видео",
        help_texts=[HelpTextItem(RoleEnum.USER, [HelpTextArgument("(видео)", "вырезает аудиодорожку из видео")])],
    )

    access = RoleEnum.TRUSTED
    attachments = [VideoAttachment]

    def start(self) -> ResponseMessage:
        source_event = self._get_video_source_event()
        att = source_event.get_all_attachments([VideoAttachment], use_fwd=False)[0]
        att.download_content()
        vh = VideoHandler(video=att, log_filter=self.event.log_filter)
        audio_track = vh.get_audio_track()
        title = self._get_audio_title(source_event)
        audio_att = self.bot.get_audio_attachment(
            _bytes=audio_track,
            peer_id=self.event.peer_id,
            message_thread_id=self.event.message_thread_id,
            filename=f"{title}.aac",
            title=title,
        )
        return ResponseMessage(ResponseMessageItem(attachments=[audio_att]))

    def _get_video_source_event(self):
        if self.event.has_attachment(VideoAttachment):
            return self.event
        return next(fwd for fwd in self.event.fwd if fwd.has_attachment(VideoAttachment))

    @staticmethod
    def _get_audio_title(source_event) -> str:
        if source_event.is_fwd and source_event.message and source_event.message.raw:
            title = source_event.message.raw
        else:
            title = "audiotrack"
        return prepare_filename(title) or "audiotrack"
