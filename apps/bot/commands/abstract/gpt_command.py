import datetime
import logging
from abc import ABC

from django.db.models import Q, Sum

from apps.bot.api.gpt.gpt import GPTAPI
from apps.bot.api.gpt.message import GPTMessages, GPTMessageRole
from apps.bot.api.gpt.models import GPTImageFormat
from apps.bot.api.gpt.response import GPTAPIImageDrawResponse, GPTAPICompletionsResponse
from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.command import Command
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Platform
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.event.event import Event
from apps.bot.classes.event.tg_event import TgEvent
from apps.bot.classes.help_text import HelpTextItemCommand
from apps.bot.classes.messages.attachments.document import DocumentAttachment
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.bot.models import Profile, Chat
from apps.bot.utils.cache import MessagesCache
from apps.bot.utils.utils import markdown_to_html
from apps.service.models import GPTPrePrompt, GPTUsage
from petrovich.settings import env

logger = logging.getLogger()


class GPTCommand(ABC, Command):
    platforms = [Platform.TG]
    priority = 90
    abstract = True

    DEFAULT_HELP_TEXT_ITEMS = [
        HelpTextItemCommand("(фраза)", "общение с ботом"),
        HelpTextItemCommand("(пересланное сообщение)", "общение с ботом с учётом пересланного сообщения"),
        HelpTextItemCommand("(текстовый файл)", "общение с ботом с учётом текстового файла")
    ]
    VISION_HELP_TEXT_ITEM = HelpTextItemCommand("(фраза) [картинка]", "общение с ботом с учётом пересланной картинки")
    DRAW_HELP_TEXT_ITEM = HelpTextItemCommand("нарисуй [альбом/портрет/квадрат] (фраза/пересланное сообщение)",
                                              "генерация картинки")

    PREPROMPT_HELP_TEXT_ITEMS = [
        HelpTextItemCommand("препромпт [конфа]", "посмотреть текущий препромпт"),
        HelpTextItemCommand("препромпт [конфа] (текст)", "добавить препромпт"),
        HelpTextItemCommand("препромпт [конфа] удалить", "удаляет препромпт")
    ]

    DEFAULT_EXTRA_TEXT = (
        "Если отвечать на сообщения бота через кнопку \"Ответить\" то будет продолжаться непрерывный диалог.\n"
        "В таком случае необязательно писать команду, можно просто текст\n\n"
        "Порядок использования препромптов в конфах:\n"
        "1) Персональный препромт конфы\n"
        "2) Персональный препромт\n"
        "3) Препромпт конфы"
    )

    def __init__(self, gpt_preprompt_provider: str, gpt_api_class: type[GPTAPI], gpt_messages_class: type[GPTMessages]):
        super().__init__()
        self.abstract = False
        self.gpt_preprompt_provider: str = gpt_preprompt_provider
        self.gpt_api_class: type[GPTAPI] = gpt_api_class
        self.gpt_messages_class: type[GPTMessages] = gpt_messages_class

    def accept(self, event: Event):
        """
        Обрабатывать ли боту команду или нет
        """

        # Стандартный обработчик
        accept = super(GPTCommand, self).accept(event)
        if accept:
            return True

        # Проверка, является ли это сообщение реплаем на другое сообщение, которое в свою очередь может быть реплаем на
        # обращение к gpt
        return bool(self._get_first_gpt_event_in_replies(event))

    # DEFAILT MENU

    def default(self, with_vision=True) -> ResponseMessageItem | None:
        """
        Дефолтное поведение при обращении к команде.
        Вызов истории и если нужно использовть vision модель, добавление картинок
        """
        messages = self.get_dialog()

        if with_vision:
            if photos := self.event.get_all_attachments([PhotoAttachment]):
                base64_photos = [photo.base64() for photo in photos]
                messages.last_message.images = base64_photos

        rmi = self.completions(messages)
        return self._send_rmi(rmi)

    def _send_rmi(self, rmi):
        rmi.peer_id = self.event.peer_id
        r = self.bot.send_response_message_item(rmi)
        if r.success:
            return None

        document = self._wrap_text_in_document(rmi.text)
        rmi.attachments = [document]
        rmi.text = "Ответ GPT содержит в себе очень много тегов, которые не распарсились. Положил ответ в файл"
        return rmi

    # MENU
    def menu_draw_image(self, use_statistics=True) -> ResponseMessageItem:
        """
        Рисование изображения
        """
        request_text, image_format = self._get_draw_image_request_text()
        gpt_api = self.gpt_api_class(log_filter=self.event.log_filter, sender=self.event.sender)
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_PHOTO, self.event.peer_id):
            response: GPTAPIImageDrawResponse = gpt_api.draw(request_text, image_format)
            if use_statistics:
                GPTUsage.add_statistics(self.event.sender, response.usage)

            attachments = []
            for image in response.get_images():
                att = self.bot.get_photo_attachment(image, send_chat_action=False)
                att.download_content()
                attachments.append(att)
        image_prompt = response.images_prompt if response.images_prompt else request_text
        answer = f'Результат генерации по запросу "{image_prompt}"'
        return ResponseMessageItem(text=answer, attachments=attachments, reply_to=self.event.message.id)

    def menu_preprompt(self) -> ResponseMessageItem:
        """
        Установка/удаление препромпта
        """

        if len(self.event.message.args) > 1 and self.event.message.args[1] in ["chat", "conference", "конфа", "чат"]:
            self.check_conversation()
            q = Q(chat=self.event.chat, author=None)
            return self._preprompt_works(2, q, 'препромпт конфы')
        else:
            if self.event.is_from_pm:
                q = Q(chat=None, author=self.event.sender)
                return self._preprompt_works(1, q, 'персональный препромпт')
            else:
                q = Q(chat=self.event.chat, author=self.event.sender)
                return self._preprompt_works(1, q, 'персональный препромпт конфы')

    def completions(self, messages: GPTMessages, use_statistics=True) -> ResponseMessageItem:
        """
        Стандартное общение с моделью
        """

        gpt_api = self.gpt_api_class(log_filter=self.event.log_filter, sender=self.event.sender)

        with ChatActivity(self.bot, ActivitiesEnum.TYPING, self.event.peer_id):
            photos = self.event.get_all_attachments([PhotoAttachment])
            response: GPTAPICompletionsResponse = gpt_api.completions(messages, use_image=bool(photos))

        if use_statistics:
            GPTUsage.add_statistics(self.event.sender, response.usage)

        return self._get_completions_rmi(response.text)

    # MESSAGES / DIALOG

    def get_dialog(self, extra_message: str | None = None) -> GPTMessages:
        """
        Получение списка всех сообщений с пользователем
        """

        self.event: TgEvent
        mc = MessagesCache(self.event.peer_id)

        history = self.gpt_messages_class()
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

        preprompt = self.get_preprompt(self.event.sender, self.event.chat)
        if preprompt:
            history.add_message(GPTMessageRole.SYSTEM, preprompt)
        history.reverse()

        user_message = self._get_user_msg(self.event)
        history.add_message(GPTMessageRole.USER, user_message)
        if extra_message:
            history.add_message(GPTMessageRole.USER, extra_message)
        return history

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
            if tg_event.message and tg_event.message.command in self.full_names:
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

    # PREPROMPT

    def _preprompt_works(self, args_slice_index: int, q: Q, is_for: str) -> ResponseMessageItem:
        """
        Обработка препромптов
        """

        q &= Q(provider=self.gpt_preprompt_provider)

        if len(self.event.message.args) > args_slice_index:
            # удалить
            if self.event.message.args[args_slice_index] == "удалить":
                GPTPrePrompt.objects.filter(q).delete()
                rmi = ResponseMessageItem(f"Удалил {is_for}")
            # обновить/создать
            else:
                preprompt = " ".join(self.event.message.args_case[args_slice_index:])
                preprompt_obj, _ = GPTPrePrompt.objects.update_or_create(
                    defaults={'text': preprompt},
                    **dict(q.children)
                )
                rmi = ResponseMessageItem(f"Обновил {is_for}: {preprompt_obj.text}")
        # посмотреть
        else:
            try:
                preprompt = GPTPrePrompt.objects.get(q).text
                rmi = ResponseMessageItem(f"Текущий {is_for}: {preprompt}")
            except GPTPrePrompt.DoesNotExist:
                rmi = ResponseMessageItem(f"Текущий {is_for} не задан")
        return rmi

    def get_preprompt(self, sender: Profile, chat: Chat) -> str | None:
        """
        Получить препромпт под текущую ситуацию (персональный в чате,в чате,в лс)
        """

        if chat:
            variants = [
                Q(author=sender, chat=chat, provider=self.gpt_preprompt_provider),
                Q(author=None, chat=chat, provider=self.gpt_preprompt_provider),
            ]
        else:
            variants = [
                Q(author=sender, chat=None, provider=self.gpt_preprompt_provider),
            ]

        for q in variants:
            try:
                return GPTPrePrompt.objects.get(q).text
            except GPTPrePrompt.DoesNotExist:
                continue
        return None

    # STATISTICS

    def _get_stat_for_user(self, profile: Profile) -> str | None:
        """
        Получение статистики
        """

        stats_all = self._get_stat_db_profile(Q(author=profile))
        if not stats_all:
            return None

        # Начало и конец предыдущего месяца
        dt_now = datetime.datetime.now()
        first_day_of_current_month = dt_now.replace(day=1)
        last_day_of_last_month = first_day_of_current_month - datetime.timedelta(days=1)
        first_day_of_last_month = last_day_of_last_month.replace(day=1)

        stats_today = self._get_stat_db_profile(
            Q(author=profile, created_at__gte=dt_now - datetime.timedelta(days=1))
        )
        stats_7_day = self._get_stat_db_profile(
            Q(author=profile, created_at__gte=dt_now - datetime.timedelta(days=7))
        )

        last_month = self._get_stat_db_profile(
            Q(author=profile, created_at__gte=first_day_of_last_month, created_at__lt=first_day_of_current_month)
        )

        current_month = self._get_stat_db_profile(
            Q(author=profile, created_at__gte=first_day_of_current_month, created_at__lt=dt_now)
        )

        return f"{profile}:\n" \
               f"Сегодня - $ {round(stats_today, 2)}\n" \
               f"7 дней - $ {round(stats_7_day, 2)}\n" \
               f"Прошлый месяц- $ {round(last_month, 2)}\n" \
               f"Текущий месяц- $ {round(current_month, 2)}\n" \
               f"Всего - $ {round(stats_all, 2)}\n"

    @staticmethod
    def _get_stat_db_profile(q):
        """
        Получение статистики в БД
        """

        res = GPTUsage.objects.filter(q).aggregate(Sum('cost')).get('cost__sum')
        return res if res else 0

    # OTHER

    def _get_completions_rmi(self, answer: str):
        """
        Пост-обработка сообщения в completions
        """
        answer = answer if answer else "{пустой ответ}"
        answer = markdown_to_html(answer, self.bot)
        pre = f"<{self.bot.PRE_TAG}>"
        if self.event.is_from_chat and pre not in answer and len(answer) > 200:
            answer = self.bot.get_quote_text(answer, expandable=True)

        if len(answer) > self.bot.MAX_MESSAGE_TEXT_LENGTH:
            document = self._wrap_text_in_document(answer)
            answer = "Твой запрос получился слишком большой. Положил ответ в файл"
            rmi = ResponseMessageItem(text=answer, attachments=[document], reply_to=self.event.message.id)
        else:
            rmi = ResponseMessageItem(text=answer, reply_to=self.event.message.id)
        return rmi

    @staticmethod
    def _wrap_text_in_document(text) -> DocumentAttachment:
        text = text.replace("\n", "<br>")
        document = DocumentAttachment()
        document.parse(text.encode('utf-8'), filename='answer.html')
        return document

    def _get_draw_image_request_text(self) -> tuple[str, GPTImageFormat | None]:
        """
        Получение текста, который хочет нарисовать пользователь
        """

        if len(self.event.message.args) > 1:
            msg_args = self.event.message.args_case[1:]

            image_format = None
            if len(self.event.message.args) > 2:
                arg1 = msg_args[0].lower()
                format_mapping = {
                    "квадрат": GPTImageFormat.SQUARE,
                    "портрет": GPTImageFormat.PORTAIR,
                    "альбом": GPTImageFormat.ALBUM
                }
                if image_format := format_mapping.get(arg1, None):
                    msg_args = msg_args[1:]

            text = " ".join(msg_args)
            return text, image_format
        elif self.event.message.quote:
            return self.event.message.quote, None
        elif self.event.fwd:
            return self.event.fwd[0].message.raw, None
        else:
            raise PWarning("Должен быть текст или пересланное сообщение")
