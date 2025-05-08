from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import AcceptExtraCommand
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Platform, Role
from apps.bot.classes.const.exceptions import PWarning, PSkipContinue
from apps.bot.classes.event.event import Event
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.video_note import VideoNoteAttachment
from apps.bot.classes.messages.attachments.voice import VoiceAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.audio.splitter import AudioSplitter
from apps.bot.utils.utils import wrap_text_in_document
from apps.gpt.api.providers.chatgpt import ChatGPTAPI
from apps.gpt.api.responses import GPTVoiceRecognitionResponse
from apps.gpt.models import Usage
from apps.gpt.providers.providers.chatgpt import ChatGPTProvider


class VoiceRecognition(AcceptExtraCommand):
    name = 'распознай'
    names = ["голос", "голосовое"]

    access = Role.USER

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
    # Обоснование: команда должна запускаться с минимальным приоритетом, потому что может быть любая другая команда,
    #  которая будет обрабатывать эти типы вложений

    priority = -100

    bot: TgBot

    @staticmethod
    def accept_extra(event: Event) -> bool:
        if event.has_voice_message or event.has_video_note:
            # check gpt key
            gpt_settings = getattr(event.sender, "gpt_settings", None)
            user_has_not_role_gpt = not event.sender.check_role(Role.GPT)
            user_has_not_personal_key = not (gpt_settings and gpt_settings.chat_gpt_key)

            if user_has_not_role_gpt and not user_has_not_personal_key:
                return False

            if event.is_from_chat and event.chat.settings.recognize_voice:
                return True
            elif event.is_from_pm:
                return True
            else:
                raise PSkipContinue()
        return False

    def start(self) -> ResponseMessage:
        # ToDo: check role?
        with ChatActivity(self.bot, ActivitiesEnum.TYPING, self.event.peer_id):
            audio_message = self.event.get_all_attachments(self.attachments)[0]
            if not audio_message.ext:
                raise PWarning("Для вложения не указано расширение (mp3/oga/wav). Укажите его для корректной работы")

            if audio_message.get_size_mb() > ChatGPTAPI.MAX_AUDIO_FILE_SIZE_MB:
                chunks = AudioSplitter.split(audio_message, ChatGPTAPI.MAX_AUDIO_FILE_SIZE_MB)

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
                content = attachment.download_content()
                response: GPTVoiceRecognitionResponse = chat_gpt_api.voice_recognition(attachment.ext, content)
                answer = response.text
                if self.event.message.mentioned:
                    Usage(
                        author=self.event.sender,
                        cost=response.usage.total_cost,
                        provider=ChatGPTProvider(),
                        model_name=response.usage.model.name
                    ).save()

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

        # Если в тексте более 200 символов, то появляется кнопка саммари
        if len(answer) > 200:
            answer = self.bot.get_quote_text(answer, expandable=True)
            button = self.bot.get_button("Саммари ", "gpt", ['_wtf'])
            keyboard = self.bot.get_inline_keyboard([button])

        # Если ответ слишком длинный - кладём в файл
        rmi = ResponseMessageItem()
        if len(answer) > self.bot.MAX_MESSAGE_TEXT_LENGTH:
            document = wrap_text_in_document(answer, 'Транскрибация.html')
            answer = "Полная транскрибация в одном файле"
            rmi.attachments = [document]

        rmi.text = answer
        rmi.reply_to = self.event.message.id
        rmi.keyboard = keyboard
        return rmi
