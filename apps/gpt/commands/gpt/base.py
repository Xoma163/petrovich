import logging
from abc import abstractmethod

from apps.bot.classes.command import Command
from apps.bot.classes.event.event import Event
from apps.bot.classes.event.tg_event import TgEvent
from apps.bot.classes.messages.attachments.document import DocumentAttachment
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.utils.cache import MessagesCache
from apps.bot.utils.utils import markdown_to_html, wrap_text_in_document
from apps.gpt.api.base import ImageEditAPIMixin
from apps.gpt.commands.gpt.functionality.completions import GPTCompletionsFunctionality
from apps.gpt.commands.gpt.functionality.image_draw import GPTImageDrawFunctionality
from apps.gpt.commands.gpt.functionality.vision import GPTVisionFunctionality
from apps.gpt.commands.gpt.mixins.key import GPTKeyMixin
from apps.gpt.commands.gpt.mixins.model_choice import GPTModelChoiceMixin
from apps.gpt.commands.gpt.mixins.preprompt import GPTPrepromptMixin
from apps.gpt.commands.gpt.mixins.statistics import GPTStatisticsMixin
from apps.gpt.messages.base import GPTMessages
from apps.gpt.messages.consts import GPTMessageRole
from apps.gpt.providers.base import GPTProvider
from petrovich.settings import env

logger = logging.getLogger(__name__)


class GPTCommand(
    Command,
    GPTKeyMixin,
    GPTModelChoiceMixin,
    GPTPrepromptMixin,
    GPTStatisticsMixin
):
    @property
    @abstractmethod
    def provider(self) -> GPTProvider:
        pass

    abstract = True

    EXTRA_TEXT = (
        "Если отвечать на сообщения бота через кнопку \"Ответить\" то будет продолжаться непрерывный диалог.\n"
        "В таком случае необязательно писать команду, можно просто текст"
    )

    def __init__(self):
        super().__init__()

    def accept(self, event: Event):
        """
        Обрабатывать ли боту команду или нет
        """
        # Стандартный обработчик
        accept = super(GPTCommand, self).accept(event)
        if accept:
            return True

        # if event.is_from_pm:
        #     return True

        # Проверка, является ли это сообщение реплаем на другое сообщение, которое в свою очередь может быть реплаем на
        # обращение к gpt
        return bool(self._get_first_gpt_event_in_replies(event))

    def start(self) -> ResponseMessage | None:
        if isinstance(self, GPTKeyMixin):
            result = self.check_key()
            if result:
                return result

        arg0 = self.event.message.args[0] if self.event.message.args else None
        edit_text_command_aliases = ["фотошоп", "photoshop"]

        if isinstance(self, GPTVisionFunctionality):
            if self.event.get_all_attachments([PhotoAttachment]) and arg0 not in edit_text_command_aliases:
                return ResponseMessage(self.menu_vision())

        menu = []
        if isinstance(self, GPTImageDrawFunctionality):
            menu.append([["нарисуй", "draw"], self.menu_image_draw])
        # ToDo: хм, а может нахер проверять фукнциональности, а проверять именно апишные классы?
        if isinstance(self.provider.api_class, ImageEditAPIMixin):
            menu.append([edit_text_command_aliases, self.menu_image_edit])

        if isinstance(self, GPTStatisticsMixin):
            menu.append([["стат", "стата", "статистика", "stat", "stats", "statistics"], self.menu_statistics])
        if isinstance(self, GPTPrepromptMixin):
            menu.append([["препромпт", "препромт", "промпт", "preprompt", "prepromp", "prompt"], self.menu_preprompt])
        if isinstance(self, GPTKeyMixin):
            menu.append([["ключ", "key"], self.menu_key])
        if isinstance(self, GPTModelChoiceMixin):
            menu.append([["модели", "models"], self.menu_models])
            menu.append([["модель", "model"], self.menu_model])
        if isinstance(self, GPTCompletionsFunctionality):
            menu.append([["_summary"], self.menu_summary])
            menu.append([['default'], self.menu_completions])

        arg0 = self.event.message.args[0] if self.event.message.args else None
        method = self.handle_menu(menu, arg0)
        answer = method()
        return ResponseMessage(answer)

    # COMMON UTILS
    def get_dialog(self, extra_message: str | None = None) -> GPTMessages:
        """
        Получение списка всех сообщений с пользователем
        """

        self.event: TgEvent
        mc = MessagesCache(self.event.peer_id)

        history = self.provider.messages_class()
        if first_event := self._get_first_gpt_event_in_replies(self.event):
            data = mc.get_messages()
            reply_to_id = self.event.fwd[0].message.id

            while True:
                raw = data.get(reply_to_id)
                tg_event = TgEvent({"message": raw})
                tg_event.setup_event()
                is_me = str(tg_event.from_id) == env.str("TG_BOT_GROUP_ID")
                if is_me:
                    if msg := self._get_bot_msg(tg_event):
                        history.add_message(GPTMessageRole.ASSISTANT, msg)
                else:
                    if msg := self._get_user_msg(tg_event):
                        history.add_message(GPTMessageRole.USER, msg)
                reply_to_id = data.get(reply_to_id, {}).get('reply_to_message', {}).get('message_id')
                if not reply_to_id or tg_event.message.id == first_event.message.id:
                    break
            if first_event.fwd:
                # unreach?
                logger.debug({"message": "gpt:175 unreach"})
                history.add_message(GPTMessageRole.USER, first_event.fwd[0].message.raw)
        # Ответ на сообщение
        elif self.event.fwd and self.event.fwd[0].message.raw:
            history.add_message(GPTMessageRole.USER, self.event.fwd[0].message.raw)

        if isinstance(self, GPTPrepromptMixin):
            preprompt = self.get_preprompt(self.event.sender, self.event.chat)
            if preprompt:
                history.add_message(GPTMessageRole.SYSTEM, preprompt)
        history.reverse()

        user_message = self._get_user_msg(self.event)
        history.add_message(GPTMessageRole.USER, user_message)
        if extra_message:
            history.add_message(GPTMessageRole.USER, extra_message)
        return history

    def get_completions_rmi(self, answer: str):
        """
        Пост-обработка сообщения в completions
        """
        answer = answer if answer else "{пустой ответ}"
        answer = markdown_to_html(answer, self.bot)
        pre = f"<{self.bot.PRE_TAG}>"
        if self.event.is_from_chat and pre not in answer and len(answer) > 200:
            answer = self.bot.get_quote_text(answer, expandable=True)

        if len(answer) > self.bot.MAX_MESSAGE_TEXT_LENGTH:
            document = wrap_text_in_document(answer, 'gpt.html')
            answer = "Твой запрос получился слишком большой. Положил ответ в файл"
            rmi = ResponseMessageItem(text=answer, attachments=[document], reply_to=self.event.message.id)
        else:
            rmi = ResponseMessageItem(text=answer, reply_to=self.event.message.id)
        return rmi

    def send_rmi(self, rmi):
        rmi.peer_id = self.event.peer_id
        r = self.bot.send_response_message_item(rmi)
        if r.success:
            return None

        document = wrap_text_in_document(rmi.text, filename='gpt.html')
        rmi.attachments = [document]
        rmi.text = "Ответ GPT содержит в себе очень много тегов, которые не распарсились. Положил ответ в файл"
        return rmi

    # UTILS
    def _get_first_gpt_event_in_replies(self, event) -> TgEvent | None:
        """
        Получение первого сообщении в серии reply сообщений
        """

        if not event.fwd:
            return None
        if not event.fwd[0].is_from_bot_me:
            return None
        mc = MessagesCache(event.peer_id)
        data = mc.get_messages()
        reply_to_id = event.fwd[0].message.id
        find_accept_event = None
        while True:
            raw = data.get(reply_to_id)
            tg_event = TgEvent({"message": raw})
            tg_event.setup_event()
            if tg_event.message and tg_event.message.command in self.full_names:  # or event.is_from_pm:
                find_accept_event = tg_event
            reply_to_id = data.get(reply_to_id, {}).get('reply_to_message', {}).get('message_id')
            if not reply_to_id:
                break
        return find_accept_event

    def _get_user_msg(self, event: TgEvent) -> str | None:
        """
        Получение текста от пользователя
        """

        if event.message.command in self.full_names:
            return self._get_common_msg(event, event.message.args_str_case)
        else:
            return self._get_common_msg(event, event.message.raw)

    def _get_bot_msg(self, event: TgEvent) -> str | None:
        return self._get_common_msg(event, event.message.raw)

    @staticmethod
    def _get_common_msg(event, text: str | None):
        documents: list[DocumentAttachment] = event.get_all_attachments([DocumentAttachment])
        text = text if text else ""
        if documents and documents[0].mime_type.is_text:
            doc_txt = documents[0].read_text()
            doc_txt_str = f"Содержимое файла: {doc_txt}"
            if not text:
                return doc_txt_str
            return f"{text}\n{doc_txt_str}"
        elif event.message.raw:
            return text
        else:
            logger.warning({
                "message": "Формирование сообщений для GPT наткнулось на сообщение, где message.text = None"
            })
            return None
