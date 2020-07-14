import io

import requests
import speech_recognition as sr
from pydub import AudioSegment

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


# ToDo: TG
class VoiceRecognition(CommonCommand):
    def __init__(self):
        names = ["распознай", "голос", "голосовое"]
        help_text = "Распознай - распознаёт голосовое сообщение"
        detail_help_text = "Распознай (Пересланное сообщение с голосовым сообщением) - распознаёт голосовое " \
                           "сообщение\n" \
                           "Если дан доступ к переписке, то распознает автоматически"
        super().__init__(names, help_text, detail_help_text, platforms=['vk', 'tg'], priority=-100, enabled=False)

    def accept(self, event):
        if have_audio_message(event):
            return True
        if event.command in self.names:
            return True

        return False

    def start(self):
        audio_messages = get_attachments_from_attachments_or_fwd(self.event, 'audio_message')
        if not audio_messages:
            return "Не нашёл голосового сообщения"
        self.bot.set_activity(self.event.peer_id, 'audiomessage')

        audio_message = audio_messages[0]

        response = requests.get(audio_message['download_url'], stream=True)
        i = io.BytesIO(response.content)
        i.seek(0)
        o = io.BytesIO()
        o.name = "recognition.wav"
        AudioSegment.from_file(i, 'mp3').export(o, format='wav')
        o.seek(0)

        r = sr.Recognizer()
        with sr.AudioFile(o) as source:
            audio = r.record(source)

        try:
            msg = r.recognize_google(audio, language='ru_RU')
            return msg
        except sr.UnknownValueError:
            return "Ничего не понял(("
        except sr.RequestError as e:
            print(str(e))
            return "Проблема с форматом"
