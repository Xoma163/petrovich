import io

import requests
import speech_recognition as sr
from pydub import AudioSegment

from apps.bot.classes.Consts import Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_attachments_from_attachments_or_fwd
from apps.bot.classes.events.Event import Event

MAX_DURATION = 20


# Если прислано голосовое - распознаёт
# Если переслано голосовое с командой - выполняет команду
# Если переслано голосовое с текстом - распознаёт
# Если переслано голосовое с неправильной командой - распознаёт
def have_audio_message(event):
    if isinstance(event, Event):
        all_attachments = event.attachments or []
        if event.fwd:
            all_attachments += event.fwd[0]['attachments']
        if all_attachments:
            for attachment in all_attachments:
                if attachment['type'] == 'audio_message':
                    return True
    else:
        all_attachments = event['message']['attachments'].copy()
        if event['fwd']:
            all_attachments += event['fwd'][0]['attachments']
        if all_attachments:
            for attachment in all_attachments:
                if attachment['type'] == 'audio_message':
                    # Костыль, чтобы при пересланном сообщении он не выполнял никакие другие команды
                    # event['message']['text'] = ''
                    return True
    return False


# ToDo: TG вложения
class VoiceRecognition(CommonCommand):
    name = 'распознай'
    names = ["голос", "голосовое"]
    help_text = "распознаёт голосовое сообщение"
    help_texts = [
        "Распознай (Пересланное сообщение с голосовым сообщением) - распознаёт голосовое сообщение\n"
        "Если дан доступ к переписке, то распознает автоматически"
    ]
    platforms = [Platform.VK, Platform.TG]
    attachments = ['audio_message']
    priority = -100

    def accept(self, event):
        if have_audio_message(event):
            return True
        return super().accept(event)

    def start(self):
        audio_messages = get_attachments_from_attachments_or_fwd(self.event, 'audio_message')
        self.bot.set_activity(self.event.peer_id, 'audiomessage')

        audio_message = audio_messages[0]

        download_url = audio_message.get('private_download_url', 'download_url')
        response = requests.get(download_url, stream=True)
        i = io.BytesIO(response.content)
        i.seek(0)
        o = io.BytesIO()
        o.name = "recognition.wav"
        try:
            input_file_format = download_url.split('.')[-1]
            if input_file_format == 'oga':
                input_file_format = 'ogg'
        except:
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
