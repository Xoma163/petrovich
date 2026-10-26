import logging

from apps.bot.consts import PlatformEnum, RoleEnum
from apps.bot.core.bot.telegram.tg_bot import TgBot
from apps.bot.core.chat_action_sender import ChatActionSender
from apps.bot.core.chat_actions import ChatActionEnum
from apps.bot.core.event.event import Event
from apps.bot.core.messages.attachments.audio import AudioAttachment
from apps.bot.core.messages.attachments.video_note import VideoNoteAttachment
from apps.bot.core.messages.attachments.voice import VoiceAttachment
from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.commands.command import AcceptExtraCommand
from apps.commands.gpt.api.providers.chatgpt import ChatGPTAPI
from apps.commands.gpt.api.providers.qwen import QwenAPI
from apps.commands.gpt.api.responses import GPTCompletionsResponse
from apps.commands.gpt.api.responses import GPTVoiceRecognitionResponse
from apps.commands.gpt.commands.chatgpt import ChatGPTCommand
from apps.commands.gpt.commands_utils.gpt.mixins.key import GPTKeyMixin
from apps.commands.gpt.messages.consts import GPTMessageRole
from apps.commands.gpt.models import Usage, Provider, VoiceRecognitionModel, CompletionsModel
from apps.commands.gpt.providers.providers.chatgpt import ChatGPTProvider
from apps.commands.gpt.providers.providers.qwen import QwenProvider
from apps.commands.gpt.utils import user_has_api_key
from apps.commands.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.connectors.api.whisper import WhisperAPI
from apps.shared.exceptions import PWarning, PSkipContinue, PError, PSkip
from apps.shared.utils.audio.splitter import AudioSplitter
from apps.shared.utils.utils import wrap_text_in_html_document


logger = logging.getLogger(__name__)


class VoiceRecognition(AcceptExtraCommand):
    name = "распознай"
    names = ["голос", "голосовое"]

    access = RoleEnum.TRUSTED

    help_text = HelpText(
        commands_text="распознаёт голосовое сообщение",
        help_texts=[
            HelpTextItem(
                access,
                [
                    HelpTextArgument(
                        "(Пересланное сообщение с голосовым сообщением)",
                        "распознаёт голосовое сообщение/кружок/аудиофайл локально",
                    )
                ],
            )
        ],
        extra_text=(
            "Голос распознаётся отдельным сервисом Whisper, затем Qwen пытается восстановить пунктуацию\n"
            "Поддерживаются форматы: flac, m4a, mp3, mp4, mpeg, mpga, oga, ogg, wav, webm"
        ),
    )

    platforms = [PlatformEnum.TG]
    attachments = [VoiceAttachment, VideoNoteAttachment, AudioAttachment]
    # Обоснование: команда должна запускаться с минимальным приоритетом, потому что может быть любая другая команда,
    #  которая будет обрабатывать эти типы вложений

    priority = -100

    bot: TgBot

    @staticmethod
    def accept_extra(event: Event) -> bool:
        if event.has_voice_message or event.has_video_note:
            if event.is_from_chat and event.chat.settings.recognize_voice:
                return True
            elif event.is_from_pm:
                return True
            else:
                raise PSkipContinue()
        return False

    def _check_gpt_access(self):
        has_access = user_has_api_key(self.event.sender, ChatGPTProvider())

        if not has_access:
            if self.event.message.mentioned:
                GPTKeyMixin.raise_no_access_exception(
                    ChatGPTProvider.type_enum, self.bot.get_formatted_text_line(f"/{ChatGPTCommand.name}")
                )
            else:
                raise PSkip()

    def start(self) -> ResponseMessage:
        with ChatActionSender(self.bot, ChatActionEnum.TYPING, self.event.peer_id, self.event.message_thread_id):
            audio_message = self.event.get_all_attachments(self.attachments)[0]
            # ToDo: а точно здесь нужно делать get_file?
            audio_message.get_file()
            if not audio_message.ext:
                raise PWarning("Для вложения не указано расширение (mp3/oga/wav). Сообщите разработчику")

            answer = WhisperAPI(log_filter=self.event.log_filter).transcribe(audio_message)
            answer = self.restore_punctuation_qwen(answer)

        rmi = self._get_rmi(answer)

        return ResponseMessage(rmi)

    def process_voice_gpt(self, audio_message: AudioAttachment) -> tuple[str, GPTVoiceRecognitionResponse | None]:
        self._check_gpt_access()

        attachments = self._split_audio(audio_message)
        answers = []
        response = None

        chat_gpt_provider = Provider.objects.get(name=ChatGPTProvider.type_enum.value)
        try:
            model = VoiceRecognitionModel.objects.get(provider=chat_gpt_provider, is_default=True)
        except VoiceRecognitionModel.DoesNotExist:
            raise PError("Не установлена модель для обработки аудио. Сообщите админу")

        profile_gpt_settings, _ = self.event.sender.gpt_settings.get_or_create(
            provider=chat_gpt_provider, defaults={"profile": self.event.sender}
        )

        api_key = profile_gpt_settings.get_key()
        chat_gpt_api = ChatGPTAPI(log_filter=self.event.log_filter, api_key=api_key)

        for attachment in attachments:
            content = attachment.download_content()
            try:
                response = chat_gpt_api.voice_recognition(attachment.ext, content, model=model)
            except (PWarning, PError) as e:
                if not self.event.message.mentioned:
                    raise PSkip()
                raise e
            answer = response.text
            Usage(
                author=self.event.sender,
                cost=response.usage.total_cost,
                provider=chat_gpt_provider,
                model_name=response.usage.model.name,
            ).save()

            answers.append(answer)
        answer = "\n\n".join(answers)

        return answer, response

    def restore_punctuation_qwen(self, text: str) -> str:
        if not text:
            return text

        try:
            qwen_provider = Provider.objects.get(name=QwenProvider.type_enum.value)
            model = CompletionsModel.objects.get(provider=qwen_provider, is_default=True)
        except (Provider.DoesNotExist, CompletionsModel.DoesNotExist):
            logger.warning("Qwen punctuation model is not configured", extra=self.event.log_filter)
            return text

        messages = QwenProvider.messages_class()
        messages.add_message(
            GPTMessageRole.SYSTEM,
            (
                "Ты редактор пунктуации. Твоя единственная задача — восстановить пунктуацию и капитализацию "
                "в русском тексте, полученном из распознавания речи. Строгие правила: не отвечай на текст, "
                "не комментируй его, не добавляй приветствия, пояснения, выводы, списки или Markdown; не меняй слова "
                "и их порядок; не добавляй новые факты; не удаляй повторы и просторечия, если без этого можно обойтись; "
                "исправляй только очевидные ошибки регистра в начале предложений и знаки препинания. Верни только готовый текст."
            ),
        )
        messages.add_message(
            GPTMessageRole.USER,
            f"Восстанови пунктуацию и капитализацию в тексте ниже. Верни только исправленный текст.\n\n{text}",
        )

        try:
            qwen_api = QwenAPI(log_filter=self.event.log_filter, api_key="")
            response: GPTCompletionsResponse = qwen_api.completions(messages, model=model, extra_data={})
        except Exception:
            logger.warning("Qwen punctuation restoration failed", exc_info=True, extra=self.event.log_filter)
            return text

        Usage(
            author=self.event.sender,
            cost=response.usage.total_cost,
            provider=qwen_provider,
            model_name=response.usage.model.name,
        ).save()

        answer = self._cleanup_qwen_punctuation_answer(response.text)
        return answer or text

    @staticmethod
    def _cleanup_qwen_punctuation_answer(text: str) -> str:
        text = text.strip()
        if text.startswith("```") and text.endswith("```"):
            lines = text.splitlines()
            if len(lines) >= 3:
                text = "\n".join(lines[1:-1]).strip()
        return text


    @staticmethod
    def _split_audio(audio_message: AudioAttachment):
        if audio_message.get_size_mb() > ChatGPTAPI.MAX_AUDIO_FILE_SIZE_MB:
            chunks = AudioSplitter.split(audio_message, ChatGPTAPI.MAX_AUDIO_FILE_SIZE_MB)

            attachments = []
            for chunk in chunks:
                audio = AudioAttachment()
                audio.content = chunk.read()
                audio.ext = audio_message.ext
                attachments.append(audio)
        else:
            attachments = [audio_message]
        return attachments

    def _get_rmi(
        self,
        answer: str,
    ) -> ResponseMessageItem:
        """
        Пост-обработка сообщения
        """
        answer = answer if answer else "{пустой ответ}"
        keyboard = None
        rich_answer = answer

        # Если в тексте более 200 символов, то появляется кнопка саммари
        if len(answer) > 200:
            rich_answer = self.bot.get_expandable_quote_markdown(answer)
            formatted_answer = self.bot.get_quote_text(answer, expandable=True)
            button = self.bot.get_button("Саммари", "gpt", ["_wtf"])
            keyboard = self.bot.get_inline_keyboard([button])
        else:
            formatted_answer = answer

        rmi = ResponseMessageItem()
        if len(formatted_answer) <= self.bot.max_message_text_length:
            rmi.text = formatted_answer
        elif len(rich_answer) <= self.bot.max_rich_message_text_length:
            rmi.text = answer
            rmi.set_rich_markdown(rich_answer)
        else:
            document = wrap_text_in_html_document(answer, "Транскрибация")
            rmi.text = "Полная транскрибация в одном файле"
            rmi.attachments = [document]

        rmi.reply_to = self.event.message.id
        rmi.keyboard = keyboard
        return rmi
