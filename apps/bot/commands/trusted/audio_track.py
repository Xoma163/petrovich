from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.utils.video.audio_track import AudioTrack


class AudioTrackCommand(Command):
    name = "аудиодорожка"

    help_text = HelpText(
        commands_text="Вырезает аудиодорожку из видео",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand("(видео)", "вырезает аудиодорожку из видео")
            ])
        ],
    )

    access = Role.TRUSTED
    attachments = [VideoAttachment]

    def start(self) -> ResponseMessage:
        att = self.event.get_all_attachments([VideoAttachment])[0]

        at = AudioTrack()
        audio_track = at.get_audio_track(att.download_content(stream=True))

        audio_att = self.bot.get_audio_attachment(audio_track)

        return ResponseMessage(ResponseMessageItem(attachments=[audio_att]))
