from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.utils.video.video_handler import VideoHandler


class AudioTrack(Command):
    name = "аудиодорожка"
    names = ["аудио"]

    help_text = HelpText(
        commands_text="Вырезает аудиодорожку из видео",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextArgument("(видео)", "вырезает аудиодорожку из видео")
            ])
        ],
    )

    access = Role.TRUSTED
    attachments = [VideoAttachment]

    def start(self) -> ResponseMessage:
        att = self.event.get_all_attachments([VideoAttachment])[0]
        vh = VideoHandler(video=att)
        audio_track = vh.get_audio_track()
        audio_att = self.bot.get_audio_attachment(audio_track)
        return ResponseMessage(ResponseMessageItem(attachments=[audio_att]))
