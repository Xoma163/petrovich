import logging
from abc import abstractmethod

from apps.bot.classes.command import Command
from apps.bot.classes.const.exceptions import PWarning, PError
from apps.bot.classes.event.event import Event
from apps.bot.classes.event.tg_event import TgEvent
from apps.bot.classes.messages.attachments.document import DocumentAttachment
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.utils.cache import MessagesCache
from apps.bot.utils.utils import markdown_to_html, wrap_text_in_document
from apps.gpt.api.base import ImageDrawAPIMixin, VisionAPIMixin, CompletionsAPIMixin
from apps.gpt.commands.gpt.functionality.completions import GPTCompletionsFunctionality
from apps.gpt.commands.gpt.functionality.image_draw import GPTImageDrawFunctionality
from apps.gpt.commands.gpt.functionality.vision import GPTVisionFunctionality
from apps.gpt.commands.gpt.mixins.key import GPTKeyMixin
from apps.gpt.commands.gpt.mixins.model_choice import GPTModelChoiceMixin
from apps.gpt.commands.gpt.mixins.preprompt import GPTPrepromptMixin
from apps.gpt.commands.gpt.mixins.statistics import GPTStatisticsMixin
from apps.gpt.messages.base import GPTMessages
from apps.gpt.messages.consts import GPTMessageRole
from apps.gpt.models import Provider, ProfileGPTSettings, GPTModel
from apps.gpt.protocols import GPTCommandProtocol
from apps.gpt.providers.base import GPTProvider
from petrovich.settings import env

logger = logging.getLogger(__name__)


class GPTCommand(
    Command,
    GPTKeyMixin,
    GPTModelChoiceMixin,
    GPTPrepromptMixin,
    GPTStatisticsMixin,
    GPTCommandProtocol
):
    abstract = True

    EXTRA_TEXT = (
        "Если отвечать на сообщения бота через кнопку \"Ответить\" то будет продолжаться непрерывный диалог.\n"
        "В таком случае необязательно писать команду, можно просто текст"
    )

    NO_DEFAULT_MODEL_ERROR_MSG = "Не установлена модель по умолчанию. Сообщите об этом админу.\n" \
                                 "Прямо сейчас вы можете просто вручную установить модель и пользоваться ей"

    RESPONSE_MESSAGE_TOO_LONG = "Твой запрос получился слишком большой. Положил ответ в файл"

    @property
    @abstractmethod
    def provider(self) -> GPTProvider:
        pass

    provider_model: Provider = None

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
        self.set_provider_model()

        if isinstance(self, GPTKeyMixin):
            result = self.check_key()
            if result:
                return result

        arg0 = self.event.message.args[0] if self.event.message.args else None
        # edit_image_command_aliases = ["фотошоп", "photoshop"]
        edit_image_command_aliases = []

        if issubclass(self.provider.api_class, VisionAPIMixin) and isinstance(self, GPTVisionFunctionality):
            if self.event.get_all_attachments([PhotoAttachment]) and arg0 not in edit_image_command_aliases:
                return ResponseMessage(self.menu_vision())

        menu = []
        if issubclass(self.provider.api_class, ImageDrawAPIMixin) and isinstance(self, GPTImageDrawFunctionality):
            menu.append([["нарисуй", "draw"], self.menu_image_draw])
        # if isinstance(self.provider.api_class, ImageEditAPIMixin):
        #     menu.append([edit_image_command_aliases, self.menu_image_edit])

        if isinstance(self, GPTStatisticsMixin):
            menu.append([["стат", "стата", "статистика", "stat", "stats", "statistics"], self.menu_statistics])
        if isinstance(self, GPTPrepromptMixin):
            menu.append([["препромпт", "препромт", "промпт", "preprompt", "prepromp", "prompt"], self.menu_preprompt])
        if isinstance(self, GPTKeyMixin):
            menu.append([["ключ", "key"], self.menu_key])
        if isinstance(self, GPTModelChoiceMixin):
            menu.append([["модели", "models"], self.menu_models])
            menu.append([["модель", "model"], self.menu_model])
        if issubclass(self.provider.api_class, CompletionsAPIMixin) and isinstance(self, GPTCompletionsFunctionality):
            menu.append([["_wtf"], self.menu_wtf])
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
            rmi = ResponseMessageItem(text=self.RESPONSE_MESSAGE_TOO_LONG, attachments=[document],
                                      reply_to=self.event.message.id)
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

    def get_api_key(self) -> str:
        """
        Получение api_key
        Сначала ищем у пользователя, потом берём общий
        """
        profile_gpt_settings = self.get_profile_gpt_settings()
        if key := profile_gpt_settings.get_key():
            return key
        return self.provider.api_key

    def get_profile_gpt_settings(self) -> ProfileGPTSettings:
        """
        Получение GPT настроек пользователя
        """
        provider = self._get_provider_model()
        gpt_settings = self.event.sender.gpt_settings
        profile_gpt_settings, _ = gpt_settings.get_or_create(
            provider=provider,
            profile=self.event.sender,
        )
        return profile_gpt_settings

    def get_model(self, model_class: type[GPTModel], field_model_name: str):
        """
        Получение модели пользователя.

        model_class: класс модели
        field_model_name - поле модели в profile_gpt_settings

        Если не найдено, то берёт стандартную модель
        """

        if user_model := self.get_user_model(field_model_name):
            return user_model
        return self.get_default_model(model_class)

    def get_user_model(self, field_model_name: str) -> GPTModel | None:
        """
        Получение модели для пользователя.


        Возвращает найденную модель для пользователя или None, если она не найдена
        """
        profile_gpt_settings = self.get_profile_gpt_settings()
        return getattr(profile_gpt_settings, field_model_name, None)

    def get_default_model(self, model_class: type[GPTModel]) -> GPTModel:
        """
        Получение модели по умолчанию
        Если такая не указана в базе, то выдаёт ошибку
        """
        try:
            return model_class.objects.get(provider=self.provider_model, is_default=True)
        except model_class.DoesNotExist:
            raise PError(self.NO_DEFAULT_MODEL_ERROR_MSG)

    def set_provider_model(self):
        if not self.provider_model:
            self.provider_model = self._get_provider_model()

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
        if event.message.raw == self.RESPONSE_MESSAGE_TOO_LONG:
            return self._get_common_msg(event, None)
        else:
            return self._get_common_msg(event, event.message.raw)


    @staticmethod
    def _get_common_msg(event, text: str | None):
        documents: list[DocumentAttachment] = event.get_all_attachments([DocumentAttachment])
        text = text if text else ""
        document = documents[0] if documents else None
        if document and (document.mime_type.is_text or document.ext.lower() in ['html', 'txt']):
            doc_txt = document.read_text()
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

    def _get_provider_model(self):
        if self.provider_model:
            return self.provider_model

        try:
            return Provider.objects.get(name=self.provider.type_enum.value)
        except Provider.DoesNotExist:
            raise PWarning("Провайдер не определён. Сообщите админу.")
