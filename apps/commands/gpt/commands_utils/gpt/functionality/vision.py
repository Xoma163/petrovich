from apps.bot.core.chat_action_sender import ChatActionSender
from apps.bot.core.chat_actions import ChatActionEnum
from apps.bot.core.messages.response_message import ResponseMessageItem
from apps.commands.gpt.api.base import GPTAPI
from apps.commands.gpt.api.responses import GPTVisionResponse
from apps.commands.gpt.messages.base import GPTMessages
from apps.commands.gpt.models import VisionModel
from apps.commands.gpt.protocols import GPTCommandProtocol, HasVision
from apps.commands.help_text import HelpTextArgument


class GPTVisionFunctionality(GPTCommandProtocol):
    VISION_HELP_TEXT_ITEMS = [
        HelpTextArgument("(фраза) [картинка]", "общение с ботом с учётом пересланной картинки")
    ]

    # MENU

    def menu_vision(self) -> ResponseMessageItem | None:
        """
        Дефолтное поведение при обращении к команде.
        Вызов истории и если нужно использовть vision модель, добавление картинок
        """
        messages = self.get_dialog()
        rmi = self.vision(messages)
        return self.send_rmi(rmi)

    # HANDLERS

    def vision(self, messages: GPTMessages) -> ResponseMessageItem:
        """
        Стандартное общение с моделью
        """
        profile_settings = self.get_profile_gpt_settings()

        gpt_api: GPTAPI | HasVision = self.provider.api_class(
            api_key=self.get_api_key(),
            log_filter=self.event.log_filter
        )

        use_callback_and_stream = profile_settings.use_stream and self.event.is_from_pm
        with ChatActionSender(self.bot, ChatActionEnum.TYPING, self.event.peer_id, self.event.message_thread_id):
            response: GPTVisionResponse = gpt_api.vision(
                messages=messages,
                model=self.get_vision_model(),
                extra_data=self.get_extra_data(),
                callback_func=self.__vision_callback if use_callback_and_stream else None,

            )

        self.add_statistics(api_response=response)

        response_text = response.text

        profile_settings = self.get_profile_gpt_settings()
        if profile_settings.use_debug:
            response_text += self.get_debug_text(response)

        return self.get_completions_rmi(response_text)

    def __vision_callback(self, text: str, draft_id: int):
        rmi = ResponseMessageItem(text=text)
        rmi.set_telegram_markdown_v2()
        rmi.peer_id = self.event.peer_id
        rmi.message_thread_id = self.event.message_thread_id

        self.bot.send_message_draft(rmi, draft_id=draft_id)

    # COMMON UTILS

    def get_vision_model(self) -> VisionModel:
        return self.get_model(VisionModel, "vision_model")

    def get_default_vision_model(self) -> VisionModel:
        return self.get_default_model(VisionModel)
