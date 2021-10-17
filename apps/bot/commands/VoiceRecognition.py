import io

import requests
import speech_recognition as sr
from pydub import AudioSegment

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.classes.messages.attachments.VoiceAttachment import VoiceAttachment
from apps.bot.utils.utils import get_attachments_from_attachments_or_fwd


class VoiceRecognition(Command):
    name = 'распознай'
    names = ["голос", "голосовое"]
    help_text = "распознаёт голосовое сообщение"
    help_texts = [
        "(Пересланное сообщение с голосовым сообщением) - распознаёт голосовое сообщение\n"
        "Если дан доступ к переписке, то распознает автоматически"
    ]
    platforms = [Platform.VK, Platform.TG]
    attachments = [VoiceAttachment]
    priority = -100

    def accept(self, event):
        if event.has_voice_message:
            return True
        return super().accept(event)

    def start(self):
        audio_messages = get_attachments_from_attachments_or_fwd(self.event, VoiceAttachment)
        self.bot.set_activity(self.event.peer_id, ActivitiesEnum.TYPING)

        audio_message = audio_messages[0]

        download_url = audio_message.get_download_url()
        response = requests.get(download_url, stream=True)
        i = io.BytesIO(response.content)
        i.seek(0)
        o = io.BytesIO()
        o.name = "recognition.wav"
        try:
            input_file_format = download_url.split('.')[-1]
            if input_file_format == 'oga':
                input_file_format = 'ogg'
        except Exception:
            input_file_format = 'mp3'
        AudioSegment.from_file(i, input_file_format).export(o, format='wav')
        o.seek(0)

        r = sr.Recognizer()
        with sr.AudioFile(o) as source:
            audio = r.record(source)

        try:
            msg = r.recognize_google(audio, language='ru_RU')
            return msg
        except sr.UnknownValueError:
            raise PWarning("Ничего не понял((")
        except sr.RequestError as e:
            print(str(e))
            raise PWarning("Проблема с форматом")
