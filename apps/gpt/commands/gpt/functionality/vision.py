from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.help_text import HelpTextArgument
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.gpt.api.responses import GPTVisionResponse
from apps.gpt.commands.gpt.protocols import HasCommandFields
from apps.gpt.messages.base import GPTMessages
from apps.gpt.models import Usage


class VisionFunctionality(HasCommandFields):
    VISION_HELP_TEXT_ITEMS = [
        HelpTextArgument("(фраза) [картинка]", "общение с ботом с учётом пересланной картинки")
    ]

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
        return self._send_rmi(rmi)

    def vision(self, messages: GPTMessages) -> ResponseMessageItem:
        """
        Стандартное общение с моделью
        """

        gpt_api = self.provider.api_class(log_filter=self.event.log_filter, sender=self.event.sender)

        with ChatActivity(self.bot, ActivitiesEnum.TYPING, self.event.peer_id):
            response: GPTVisionResponse = gpt_api.vision(messages)

        Usage.add_statistics(self.event.sender, response.usage, provider=self.provider)

        return self._get_completions_rmi(response.text)
