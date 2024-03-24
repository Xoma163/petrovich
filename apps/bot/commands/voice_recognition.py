import io

import speech_recognition as sr
from pydub import AudioSegment

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import AcceptExtraCommand
from apps.bot.classes.const.consts import Platform, Role
from apps.bot.classes.const.exceptions import PWarning, PSkip
from apps.bot.classes.event.event import Event
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.videonote import VideoNoteAttachment
from apps.bot.classes.messages.attachments.voice import VoiceAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class VoiceRecognition(AcceptExtraCommand):
    name = 'распознай'
    names = ["голос", "голосовое"]

    help_text = HelpText(
        commands_text="распознаёт голосовое сообщение",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand("(Пересланное сообщение с голосовым сообщением)", "распознаёт голосовое сообщение")
            ])
        ],
        extra_text=(
            "Если дан доступ к переписке, то распознает автоматически"
        )
    )

    platforms = [Platform.TG]
    attachments = [VoiceAttachment, VideoNoteAttachment, AudioAttachment]
    priority = -100

    bot: TgBot

    @staticmethod
    def accept_extra(event: Event) -> bool:
        if event.has_voice_message:
            if event.is_from_chat and event.chat.settings.recognize_voice:
                return True
            elif event.is_from_pm:
                return True
            else:
                raise PSkip()
        return False

    def start(self) -> ResponseMessage:
        audio_messages = self.event.get_all_attachments([VoiceAttachment, VideoNoteAttachment, AudioAttachment])
        audio_message = audio_messages[0]

        i = audio_message.get_bytes_io_content(self.event.peer_id)
        i.seek(0)
        o = io.BytesIO()
        o.name = "recognition.wav"

        input_file_format = None
        try:
            if audio_message.ext == 'oga':
                input_file_format = 'ogg'
        except Exception:
            input_file_format = 'mp3'
        AudioSegment.from_file(i, input_file_format).export(o, format='wav')
        o.seek(0)

        r = sr.Recognizer()
        with sr.AudioFile(o) as source:
            audio = r.record(source)

        reply_to = self.event.message.id
        try:
            answer: str = r.recognize_google(audio, language='ru_RU', pfilter=0)
        except sr.UnknownValueError:
            raise PWarning("Ничего не понял((", reply_to=reply_to)
        except sr.RequestError:
            raise PWarning("Проблема с форматом", reply_to=reply_to)

        spoiler_text = "спойлер"
        if spoiler_text in answer.lower():
            spoiler_index = answer.lower().index(spoiler_text)
            text_before_spoiler = answer[:spoiler_index]
            text_after_spoiler = answer[spoiler_index + len(spoiler_text):]

            answer = text_before_spoiler + self.bot.get_bold_text(spoiler_text) + self.bot.get_spoiler_text(
                text_after_spoiler)
        return ResponseMessage(ResponseMessageItem(text=answer, reply_to=reply_to))
