from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.help_text import HelpTextArgument
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.gpt.api.base import GPTAPI
from apps.gpt.api.responses import GPTVisionResponse
from apps.gpt.messages.base import GPTMessages
from apps.gpt.models import VisionModel
from apps.gpt.protocols import GPTCommandProtocol, HasVision


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

        # vision
        photos = self.event.get_all_attachments([PhotoAttachment])
        base64_photos = [photo.base64() for photo in photos]
        messages.last_message.images = base64_photos

        rmi = self.vision(messages)
        return self.send_rmi(rmi)

    # HANDLERS

    def vision(self, messages: GPTMessages) -> ResponseMessageItem:
        """
        Стандартное общение с моделью
        """

        gpt_api: GPTAPI | HasVision = self.provider.api_class(
            api_key=self.get_api_key(),
            log_filter=self.event.log_filter
        )

        with ChatActivity(self.bot, ActivitiesEnum.TYPING, self.event.peer_id):
            response: GPTVisionResponse = gpt_api.vision(
                messages=messages,
                model=self.get_vision_model(),
                extra_data=self.get_extra_data()
            )

        self.add_statistics(api_response=response)

        return self.get_completions_rmi(response.text)

    # COMMON UTILS

    def get_vision_model(self) -> VisionModel:
        return self.get_model(VisionModel, "vision_model")

    def get_default_vision_model(self) -> VisionModel:
        return self.get_default_model(VisionModel)
