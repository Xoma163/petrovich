import logging

from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.help_text import HelpTextArgument
from apps.bot.classes.messages.attachments.document import DocumentAttachment
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.gpt.api.base import GPTAPI
from apps.gpt.api.responses import GPTCompletionsResponse
from apps.gpt.enums import GPTReasoningEffortLevel, GPTVerbosityLevel
from apps.gpt.messages.base import GPTMessages
from apps.gpt.messages.consts import GPTMessageRole
from apps.gpt.models import CompletionsModel, VoiceRecognitionModel
from apps.gpt.protocols import HasCompletions, GPTCommandProtocol

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
            history.add_message(GPTMessageRole.SYSTEM, preprompt)

        history.add_message(GPTMessageRole.USER, self.DEFAULT_WTF_PROMPT)
        history.add_message(GPTMessageRole.USER, text)

        rmi = self.completions(history)
        return self.send_rmi(rmi)

    # HANDLERS

    def completions(self, messages: GPTMessages) -> ResponseMessageItem:
        """
        Стандартное общение с моделью
        """

        gpt_api: GPTAPI | HasCompletions = self.provider.api_class(
            api_key=self.get_api_key(),
            log_filter=self.event.log_filter,
        )

        with ChatActivity(self.bot, ActivitiesEnum.TYPING, self.event.peer_id):
            response: GPTCompletionsResponse = gpt_api.completions(
                messages,
                model=self.get_completions_model(),
                extra_data=self.get_extra_data()
            )

        self.add_statistics(api_response=response)

        return self.get_completions_rmi(response.text)

    # COMMON UTILS

    def get_completions_model(self) -> CompletionsModel:
        return self.get_model(CompletionsModel, "completions_model")

    def get_default_completions_model(self) -> CompletionsModel:
        return self.get_default_model(CompletionsModel)

    def get_extra_data(self) -> dict:
        from apps.gpt.commands.gpt.providers.chatgpt import ChatGPTCommand

        if isinstance(self, ChatGPTCommand):
            default_reasoning_effort_level = GPTReasoningEffortLevel.MEDIUM
            default_verbosity_level = GPTVerbosityLevel.MEDIUM
            profile_settings = self.get_profile_gpt_settings()
            return {
                'effort_level': profile_settings.gpt_5_settings_reasoning_effort_level or default_reasoning_effort_level,
                'verbosity_level': profile_settings.gpt_5_settings_verbosity_level or default_verbosity_level
            }
        return {}

    # UTILS

    # ToDo это здесь временно

    def get_voice_recognition_model(self) -> VoiceRecognitionModel:
        return self.get_model(VoiceRecognitionModel, "voice_recognition_model")

    def get_default_voice_recognition_model(self) -> CompletionsModel:
        return self.get_default_model(VoiceRecognitionModel)
