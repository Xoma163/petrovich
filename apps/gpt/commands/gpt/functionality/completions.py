import logging
from typing import Union

from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.help_text import HelpTextArgument
from apps.bot.classes.messages.attachments.document import DocumentAttachment
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.gpt.api.base import GPTAPI
from apps.gpt.api.responses import GPTCompletionsResponse
from apps.gpt.messages.base import GPTMessages
from apps.gpt.messages.consts import GPTMessageRole
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
        rmi = self._completions(messages)
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

        rmi = self._completions(history)
        return self.send_rmi(rmi)

    # HANDLERS

    def _completions(self, messages: GPTMessages) -> ResponseMessageItem:
        """
        Стандартное общение с моделью
        """

        gpt_api: Union[GPTAPI, HasCompletions] = self.provider.api_class(
            log_filter=self.event.log_filter,
            sender=self.event.sender
        )

        with ChatActivity(self.bot, ActivitiesEnum.TYPING, self.event.peer_id):
            response: GPTCompletionsResponse = gpt_api.completions(messages)

        self.add_statistics(api_response=response)

        return self.get_completions_rmi(response.text)

    # UTILS
