import io

import requests
import speech_recognition as sr
from pydub import AudioSegment

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PWarning, PSkip
from apps.bot.classes.messages.attachments.VideoNoteAttachment import VideoNoteAttachment
from apps.bot.classes.messages.attachments.VoiceAttachment import VoiceAttachment
from apps.bot.utils.utils import get_tg_bold_text, get_tg_spoiler_text


class VoiceRecognition(Command):
    name = 'распознай'
    names = ["голос", "голосовое"]
    help_text = "распознаёт голосовое сообщение"
    help_texts = ["(Пересланное сообщение с голосовым сообщением) - распознаёт голосовое сообщение"]
    help_texts_extra = "Если дан доступ к переписке, то распознает автоматически"
    platforms = [Platform.TG]
    attachments = [VoiceAttachment, VideoNoteAttachment]
    priority = -100

    @staticmethod
    def accept_extra(event):
        if event.has_voice_message:
            if event.is_from_chat and event.chat.recognize_voice:
                return True
            elif event.is_from_pm:
                return True
            else:
                raise PSkip()
        return False

    def start(self):
        audio_messages = self.event.get_all_attachments([VoiceAttachment, VideoNoteAttachment])
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

        r = PFilterGoogleRecognizer()
        with sr.AudioFile(o) as source:
            audio = r.record(source)

        reply_to = self.event.message.id
        try:
            msg: str = r.recognize_google(audio, language='ru_RU', pfilter=0)
            # return {'text': msg, 'reply_to': reply_to}
        except sr.UnknownValueError:
            raise PWarning("Ничего не понял((", reply_to=reply_to)
        except sr.RequestError as e:
            print(str(e))
            raise PWarning("Проблема с форматом")

        if self.event.platform != Platform.TG:
            return msg

        spoiler_text = "спойлер"
        if spoiler_text not in msg.lower():
            return msg

        spoiler_index = msg.lower().index(spoiler_text)
        text_before_spoiler = msg[:spoiler_index]
        text_after_spoiler = msg[spoiler_index + len(spoiler_text):]

        return text_before_spoiler + get_tg_bold_text(spoiler_text) + get_tg_spoiler_text(text_after_spoiler)


# переопределение класса для отключения pFilter
class PFilterGoogleRecognizer(sr.Recognizer):
    def recognize_google(self, audio_data, key=None, language="en-US", show_all=False, pfilter=1):

        assert isinstance(audio_data, sr.AudioData), "``audio_data`` must be audio data"
        assert key is None or isinstance(key, str), "``key`` must be ``None`` or a string"
        assert isinstance(language, str), "``language`` must be a string"

        flac_data = audio_data.get_flac_data(
            convert_rate=None if audio_data.sample_rate >= 8000 else 8000,  # audio samples must be at least 8 kHz
            convert_width=2  # audio samples must be 16-bit
        )
        if key is None: key = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
        url = "https://www.google.com/speech-api/v2/recognize?{}".format(sr.urlencode({
            "client": "chromium",
            "lang": language,
            "key": key,
            "pFilter": pfilter
        }))
        request = sr.Request(url, data=flac_data,
                             headers={"Content-Type": "audio/x-flac; rate={}".format(audio_data.sample_rate)})

        # obtain audio transcription results
        try:
            response = sr.urlopen(request, timeout=self.operation_timeout)
        except sr.HTTPError as e:
            raise sr.RequestError("recognition request failed: {}".format(e.reason))
        except sr.URLError as e:
            raise sr.RequestError("recognition connection failed: {}".format(e.reason))
        response_text = response.read().decode("utf-8")

        # ignore any blank blocks
        actual_result = []
        for line in response_text.split("\n"):
            if not line: continue
            result = sr.json.loads(line)["result"]
            if len(result) != 0:
                actual_result = result[0]
                break

        # return results
        if show_all: return actual_result
        if not isinstance(actual_result, dict) or len(
                actual_result.get("alternative", [])) == 0: raise sr.UnknownValueError()

        if "confidence" in actual_result["alternative"]:
            # return alternative with highest confidence score
            best_hypothesis = max(actual_result["alternative"], key=lambda alternative: alternative["confidence"])
        else:
            # when there is no confidence available, we arbitrarily choose the first hypothesis.
            best_hypothesis = actual_result["alternative"][0]
        if "transcript" not in best_hypothesis: raise sr.UnknownValueError()
        return best_hypothesis["transcript"]
