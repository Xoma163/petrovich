from apps.bot.consts import RoleEnum
from apps.bot.core.messages.attachments.video import VideoAttachment
from apps.bot.core.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.commands.command import Command
from apps.commands.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.shared.utils.video.video_handler import VideoHandler


# ToDo: mp3
class AudioTrack(Command):
    name = "аудиодорожка"
    names = ["аудио"]

    help_text = HelpText(
        commands_text="Вырезает аудиодорожку из видео",
        help_texts=[
            HelpTextItem(RoleEnum.USER, [
                HelpTextArgument("(видео)", "вырезает аудиодорожку из видео")
            ])
        ],
    )

    access = RoleEnum.TRUSTED
    attachments = [VideoAttachment]

    def start(self) -> ResponseMessage:
        att = self.event.get_all_attachments([VideoAttachment])[0]
        att.download_content()
        vh = VideoHandler(video=att)
        audio_track = vh.get_audio_track()
        audio_att = self.bot.get_audio_attachment(
            _bytes=audio_track,
            peer_id=self.event.peer_id,
            message_thread_id=self.event.message_thread_id,
            filename='audiotrack.aac'
        )
        return ResponseMessage(ResponseMessageItem(attachments=[audio_att]))
