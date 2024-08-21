from apps.bot.api.gpt.chatgptapi import ChatGPTAPI
from apps.bot.api.gpt.response import GPTAPIVoiceRecognitionResponse
from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import AcceptExtraMixin
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Platform, Role
from apps.bot.classes.const.exceptions import PSkip, PWarning
from apps.bot.classes.event.event import Event
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.document import DocumentAttachment
from apps.bot.classes.messages.attachments.video_note import VideoNoteAttachment
from apps.bot.classes.messages.attachments.voice import VoiceAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.audio.splitter import AudioSplitter
from apps.service.models import GPTUsage


class VoiceRecognition(AcceptExtraMixin):
    name = 'распознай'
    names = ["голос", "голосовое"]

    access = Role.USER
    chat_gpt_key = True

    help_text = HelpText(
        commands_text="распознаёт голосовое сообщение",
        help_texts=[
            HelpTextItem(access, [
                HelpTextArgument(
                    "(Пересланное сообщение с голосовым сообщением)",
                    "распознаёт голосовое сообщение/кружок/аудиофайл на основе ChatGPT"
                )
            ])
        ],
        extra_text=(
            "Если дан доступ к переписке и указан gpt api key, то распознает автоматически\n"
            "Поддерживаются форматы: flac, m4a, mp3, mp4, mpeg, mpga, oga, ogg, wav, webm"
        )
    )

    platforms = [Platform.TG]
    attachments = [VoiceAttachment, VideoNoteAttachment, AudioAttachment]
    priority = -100

    bot: TgBot

    MAX_FILE_SIZE_MB = 24

    @staticmethod
    def accept_extra(event: Event) -> bool:
        if event.has_voice_message or event.has_video_note:
            # check gpt key
            if not event.sender.check_role(Role.TRUSTED) and not event.sender.settings.chat_gpt_key:
                return False

            if event.is_from_chat and event.chat.settings.recognize_voice:
                return True
            elif event.is_from_pm:
                return True
            else:
                raise PSkip()
        return False

    def start(self) -> ResponseMessage:
        with ChatActivity(self.bot, ActivitiesEnum.TYPING, self.event.peer_id):
            audio_message = self.event.get_all_attachments(self.attachments)[0]
            if not audio_message.ext:
                raise PWarning("Для вложения не указано расширение (mp3/oga/wav). Укажите его для корректной работы")

            if audio_message.get_size_mb() > self.MAX_FILE_SIZE_MB:
                chunks = AudioSplitter.split(audio_message, self.MAX_FILE_SIZE_MB)

                attachments = []
                for chunk in chunks:
                    audio = AudioAttachment()
                    audio.content = chunk
                    audio.ext = audio_message.ext
                    attachments.append(audio)
            else:
                attachments = [audio_message]

            answers = []
            for attachment in attachments:
                chat_gpt_api = ChatGPTAPI(log_filter=self.event.log_filter, sender=self.event.sender)
                response: GPTAPIVoiceRecognitionResponse = chat_gpt_api.recognize_voice(attachment)
                answer = response.text
                if self.event.message.mentioned:
                    GPTUsage.add_statistics(self.event.sender, response.usage)

                answers.append(answer)
            answer = "\n\n".join(answers)

        rmi = self._get_rmi(answer)
        return ResponseMessage(rmi)

    def _get_rmi(
            self,
            answer: str,
    ) -> ResponseMessageItem:
        """
        Пост-обработка сообщения
        """
        answer = answer if answer else "{пустой ответ}"
        keyboard = None
        if len(answer) > 200:
            answer = self.bot.get_quote_text(answer, expandable=True)
            button = self.bot.get_button("Саммари", "gpt", ['_summary'])
            keyboard = self.bot.get_inline_keyboard([button])
        # Если ответ слишком длинный - кладём в файл
        if len(answer) > self.bot.MAX_MESSAGE_TEXT_LENGTH:
            document = self._wrap_text_in_document(answer, 'Транскрибация.html')
            answer = "Полная транскрибация в одном файле"
            rmi = ResponseMessageItem(text=answer, attachments=[document], reply_to=self.event.message.id,
                                      keyboard=keyboard)
        else:
            rmi = ResponseMessageItem(text=answer, reply_to=self.event.message.id, keyboard=keyboard)
        return rmi

    @staticmethod
    def _wrap_text_in_document(text, filename) -> DocumentAttachment:
        text = text.replace("\n", "<br>")
        document = DocumentAttachment()
        document.parse(text.encode('utf-8-sig'), filename=f'Транскрибация {filename} файла.html')
        return document
