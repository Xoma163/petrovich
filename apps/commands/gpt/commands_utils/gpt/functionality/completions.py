import logging

from apps.bot.core.chat_action_sender import ChatActionSender
from apps.bot.core.chat_actions import ChatActionEnum
from apps.bot.core.messages.attachments.document import DocumentAttachment
from apps.bot.core.messages.response_message import ResponseMessageItem
from apps.bot.core.messages.telegram.parse_mode import TelegramParseMode
from apps.commands.gpt.api.base import GPTAPI
from apps.commands.gpt.api.responses import GPTCompletionsResponse
from apps.commands.gpt.messages.base import GPTMessages
from apps.commands.gpt.messages.consts import GPTMessageRole
from apps.commands.gpt.models import CompletionsModel, VoiceRecognitionModel
from apps.commands.gpt.protocols import HasCompletions, GPTCommandProtocol
from apps.commands.help_text import HelpTextArgument

logger = logging.getLogger()


class GPTCompletionsFunctionality(GPTCommandProtocol):
    COMPLETIONS_HELP_TEXT_ITEMS = [
        HelpTextArgument("(фраза)", "общение с ботом"),
        HelpTextArgument("(пересланное сообщение)", "общение с ботом с учётом пересланного сообщения"),
        HelpTextArgument("(текстовый файл)", "общение с ботом с учётом текстового файла")
    ]

    DEFAULT_WTF_PROMPT = "Я пришлю тебе голосовое сообщение. Сделай саммари по нему, сократи и донеси суть, но не теряй важных деталей"

    # MENU

    def menu_completions(self) -> ResponseMessageItem | None:
        """
        Дефолтное поведение при обращении к команде.
        Вызов истории и если нужно использовть vision модель, добавление картинок
        """
        messages = self.get_dialog()
        rmi = self.completions(messages)
        return self.send_rmi(rmi)

    def menu_wtf(self):
        message = self.event.raw['callback_query']['message']

        documents: list[DocumentAttachment] = self.event.get_all_attachments([DocumentAttachment])
        if documents and documents[0].mime_type.is_text:
            text = documents[0].read_text()
        else:
            text = message.get('text')

        history = self.provider.messages_class()

        preprompt = self.get_preprompt(self.event.sender, self.event.chat)
        if preprompt:
            history.add_message(GPTMessageRole.SYSTEM, preprompt.text)

        history.add_message(GPTMessageRole.USER, self.DEFAULT_WTF_PROMPT)
        history.add_message(GPTMessageRole.USER, text)

        rmi = self.completions(history)
        return self.send_rmi(rmi)

    # HANDLERS

    def completions(self, messages: GPTMessages) -> ResponseMessageItem:
        """
        Стандартное общение с моделью
        """
        profile_settings = self.get_profile_gpt_settings()

        gpt_api: GPTAPI | HasCompletions = self.provider.api_class(
            api_key=self.get_api_key(),
            log_filter=self.event.log_filter,
        )

        use_callback_and_stream = profile_settings.use_stream and self.event.is_from_pm
        with ChatActionSender(self.bot, ChatActionEnum.TYPING, self.event.peer_id, self.event.message_thread_id):
            response: GPTCompletionsResponse = gpt_api.completions(
                messages,
                model=self.get_completions_model(),
                extra_data=self.get_extra_data(),
                callback_func=self.__completions_callback if use_callback_and_stream else None,
            )

        self.add_statistics(api_response=response)

        response_text = response.text

        profile_settings = self.get_profile_gpt_settings()
        if profile_settings.use_debug:
            response_text += self.get_debug_text(response)

        return self.get_completions_rmi(response_text)

    def __completions_callback(self, text: str, draft_id: int):
        rmi = ResponseMessageItem(text=text)
        rmi.set_telegram_markdown_v2()

        self.bot.send_message_draft(
            chat_id=self.event.peer_id,
            draft_id=draft_id,
            text=rmi.text,
            message_thread_id=self.event.message_thread_id,
            parse_mode=TelegramParseMode.MARKDOWN_V2
        )

    # COMMON UTILS

    def get_completions_model(self) -> CompletionsModel:
        return self.get_model(CompletionsModel, "completions_model")

    def get_default_completions_model(self) -> CompletionsModel:
        return self.get_default_model(CompletionsModel)

    # UTILS

    # ToDo это здесь временно

    def get_voice_recognition_model(self) -> VoiceRecognitionModel:
        return self.get_model(VoiceRecognitionModel, "voice_recognition_model")

    def get_default_voice_recognition_model(self) -> CompletionsModel:
        return self.get_default_model(VoiceRecognitionModel)
