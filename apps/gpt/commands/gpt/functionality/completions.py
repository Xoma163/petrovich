import logging

from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.help_text import HelpTextArgument
from apps.bot.classes.messages.attachments.document import DocumentAttachment
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.gpt.api.responses import GPTCompletionsResponse
from apps.gpt.commands.gpt.protocols import HasCommandFields
from apps.gpt.messages.base import GPTMessages
from apps.gpt.messages.consts import GPTMessageRole
from apps.gpt.models import Usage

logger = logging.getLogger()


class CompletionsFunctionality(HasCommandFields):
    COMPLETIONS_HELP_TEXT_ITEMS = [
        HelpTextArgument("(фраза)", "общение с ботом"),
        HelpTextArgument("(пересланное сообщение)", "общение с ботом с учётом пересланного сообщения"),
        HelpTextArgument("(текстовый файл)", "общение с ботом с учётом текстового файла")
    ]

    def menu_completions(self) -> ResponseMessageItem | None:
        """
        Дефолтное поведение при обращении к команде.
        Вызов истории и если нужно использовть vision модель, добавление картинок
        """
        messages = self.get_dialog()
        rmi = self.completions(messages)
        return self._send_rmi(rmi)

    def completions(self, messages: GPTMessages) -> ResponseMessageItem:
        """
        Стандартное общение с моделью
        """

        gpt_api = self.provider.api_class(log_filter=self.event.log_filter, sender=self.event.sender)

        with ChatActivity(self.bot, ActivitiesEnum.TYPING, self.event.peer_id):
            response: GPTCompletionsResponse = gpt_api.completions(messages)

        Usage.add_statistics(self.event.sender, response.usage, provider=self.provider)

        return self._get_completions_rmi(response.text)

    def menu_summary(self):
        PROMPT = "Я пришлю тебе голосовое сообщение. Сделай саммари по нему, сократи и донеси суть, но не теряй важных деталей"
        message = self.event.raw['callback_query']['message']

        documents: list[DocumentAttachment] = self.event.get_all_attachments([DocumentAttachment])
        if documents and documents[0].mime_type.is_text:
            text = documents[0].read_text()
        elif message_text := message.get('text'):
            text = message_text
        # self.get_dialog()
        history = self.provider.messages_class()

        preprompt = self.get_preprompt(self.event.sender, self.event.chat)
        if preprompt:
            history.add_message(GPTMessageRole.SYSTEM, preprompt)

        history.add_message(GPTMessageRole.USER, PROMPT)
        history.add_message(GPTMessageRole.USER, text)

        rmi = self.completions(history)
        return self._send_rmi(rmi)
