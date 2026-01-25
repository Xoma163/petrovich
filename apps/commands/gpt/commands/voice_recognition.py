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
from apps.commands.gpt.api.responses import GPTVoiceRecognitionResponse
from apps.commands.gpt.commands.chatgpt import ChatGPTCommand
from apps.commands.gpt.commands_utils.gpt.mixins.key import GPTKeyMixin
from apps.commands.gpt.models import Usage, Provider, VoiceRecognitionModel
from apps.commands.gpt.providers.providers.chatgpt import ChatGPTProvider
from apps.commands.gpt.utils import user_has_api_key
from apps.commands.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.shared.exceptions import PWarning, PSkipContinue, PError, PSkip
from apps.shared.utils.audio.splitter import AudioSplitter
from apps.shared.utils.utils import wrap_text_in_document


class VoiceRecognition(AcceptExtraCommand):
    name = 'распознай'
    names = ["голос", "голосовое"]

    access = RoleEnum.TRUSTED

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
            "Если указан chatgpt api_key, то распознает автоматически\n"
            "Поддерживаются форматы: flac, m4a, mp3, mp4, mpeg, mpga, oga, ogg, wav, webm"
        )
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
            has_access = user_has_api_key(event.sender, ChatGPTProvider())
            if has_access:
                return True

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
                    ChatGPTProvider.type_enum,
                    self.bot.get_formatted_text_line(f'/{ChatGPTCommand.name}')
                )
            else:
                raise PSkip()


    def start(self) -> ResponseMessage:
        self._check_gpt_access()

        with ChatActionSender(self.bot, ChatActionEnum.TYPING, self.event.peer_id):
            audio_message = self.event.get_all_attachments(self.attachments)[0]
            audio_message.get_file()
            if not audio_message.ext:
                raise PWarning("Для вложения не указано расширение (mp3/oga/wav). Сообщите разработчику")

            attachments = self._split_audio(audio_message)
            answers = []

            chat_gpt_provider = Provider.objects.get(name=ChatGPTProvider.type_enum.value)
            try:
                model = VoiceRecognitionModel.objects.get(provider=chat_gpt_provider, is_default=True)
            except VoiceRecognitionModel.DoesNotExist:
                raise PError("Не установлена модель для обработки аудио. Сообщите админу")

            profile_gpt_settings, created = self.event.sender.gpt_settings.get_or_create(
                provider=chat_gpt_provider,
                defaults={'profile': self.event.sender}
            )

            api_key = profile_gpt_settings.get_key()
            chat_gpt_api = ChatGPTAPI(log_filter=self.event.log_filter, api_key=api_key)

            for attachment in attachments:
                content = attachment.download_content()
                try:
                    response: GPTVoiceRecognitionResponse = chat_gpt_api.voice_recognition(
                        attachment.ext,
                        content,
                        model=model
                    )
                except (PWarning, PError) as e:
                    if not self.event.message.mentioned:
                        raise PSkip()
                    raise e
                answer = response.text
                Usage(
                    author=self.event.sender,
                    cost=response.usage.total_cost,
                    provider=chat_gpt_provider,
                    model_name=response.usage.model.name
                ).save()

                answers.append(answer)
            answer = "\n\n".join(answers)

        rmi = self._get_rmi(answer)

        if profile_gpt_settings.use_debug:
            rmi.text += ChatGPTCommand.get_debug_text(response)

        return ResponseMessage(rmi)

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

        # Если в тексте более 200 символов, то появляется кнопка саммари
        if len(answer) > 200:
            answer = self.bot.get_quote_text(answer, expandable=True)
            button = self.bot.get_button("Саммари", "gpt", ['_wtf'])
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
