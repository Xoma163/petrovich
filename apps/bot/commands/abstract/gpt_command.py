import datetime

from django.db.models import Q, Sum

from apps.bot.api.gpt.response import GPTAPICompletionsResponse, GPTAPIImageDrawResponse
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


class GPTCommand(Command):
    platforms = [Platform.TG]
    abstract = True

    DEFAULT_HELP_TEXT_ITEMS = [
        HelpTextItemCommand("(фраза)", "общение с ботом"),
        HelpTextItemCommand("(пересланное сообщение)", "общение с ботом")
    ]
    VISION_HELP_TEXT_ITEM = HelpTextItemCommand("(фраза) [картинка]", "общение с ботом с учётом пересланной картинки")
    DRAW_HELP_TEXT_ITEM = HelpTextItemCommand("нарисуй (фраза/пересланное сообщение)", "генерация картинки")

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

    PREPROMPT_PROVIDER = None
    GPT_API_CLASS = None

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

    def default(self, with_vision=True) -> ResponseMessageItem:
        """
        Дефолтное поведение при обращении к команде.
        Вызов истории и если нужно использовть vision модель, добавление картинок
        """
        messages = self.get_dialog()

        if with_vision:
            if photos := self.event.get_all_attachments([PhotoAttachment]):
                photos_data = []
                for photo in photos:
                    base64 = photo.base64()
                    photos_data = [({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64}"}})]
                messages[-1]['content'] = [{"type": "text", "text": messages[-1]['content']}]
                messages[-1]['content'] += photos_data

        return self.completions(messages)

    # MENU
    def menu_draw_image(self, use_statistics=True) -> ResponseMessageItem:
        """
        Рисование изображения
        """
        request_text = self._get_draw_image_request_text()
        gpt_api = self.GPT_API_CLASS(log_filter=self.event.log_filter, sender=self.event.sender)
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_PHOTO, self.event.peer_id):
            response: GPTAPIImageDrawResponse = gpt_api.draw(request_text)
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

    def completions(self, messages, use_statistics=True) -> ResponseMessageItem:
        """
        Стандартное общение с моделью
        """

        gpt_api = self.GPT_API_CLASS(log_filter=self.event.log_filter, sender=self.event.sender)

        with ChatActivity(self.bot, ActivitiesEnum.TYPING, self.event.peer_id):
            photos = self.event.get_all_attachments([PhotoAttachment])
            response: GPTAPICompletionsResponse = gpt_api.completions(messages, use_image=bool(photos))

        if use_statistics:
            GPTUsage.add_statistics(self.event.sender, response.usage)

        return self._get_completions_rm(response.text)

    # MESSAGES / DIALOG

    def get_dialog(self, extra_message: str | None = None) -> list:
        """
        Получение списка всех сообщений с пользователем
        """

        self.event: TgEvent
        user_message = self._get_user_msg(self.event)
        mc = MessagesCache(self.event.peer_id)
        data = mc.get_messages()
        preprompt = self.get_preprompt(self.event.sender, self.event.chat, self.PREPROMPT_PROVIDER)

        history = []
        if not self.event.fwd:
            if preprompt:
                history.append({"role": "system", "content": preprompt})
            history.append({'role': "user", 'content': user_message})
            if extra_message:
                history.append({'role': "user", 'content': extra_message})
            return history

        reply_to_id = self.event.fwd[0].message.id
        history = []
        if first_event := self._get_first_gpt_event_in_replies(self.event):
            while True:
                raw = data.get(reply_to_id)
                tg_event = TgEvent({"message": raw})
                tg_event.setup_event()
                is_me = str(tg_event.from_id) == env.str("TG_BOT_GROUP_ID")
                if is_me:
                    history.append({'role': 'assistant', 'content': tg_event.message.raw})
                else:
                    msg = self._get_user_msg(tg_event)
                    history.append({'role': "user", 'content': msg})
                reply_to_id = data.get(reply_to_id, {}).get('reply_to_message', {}).get('message_id')
                if not reply_to_id or tg_event.message.id == first_event.message.id:
                    break
            if first_event.fwd:
                history.append({'role': "user", 'content': first_event.fwd[0].message.raw})
        else:
            if self.event.fwd[0].message.raw:
                history.append({'role': "user", 'content': self.event.fwd[0].message.raw})

        if preprompt:
            history.append({"role": "system", "content": preprompt})
        history = list(reversed(history))
        history.append({'role': "user", 'content': user_message})
        if extra_message:
            history.append({'role': "user", 'content': extra_message})
        return history

    def _get_first_gpt_event_in_replies(self, event) -> TgEvent | None:
        """
        Получение первого сообщении в серии reply сообщений
        """

        mc = MessagesCache(event.peer_id)
        data = mc.get_messages()
        if not event.fwd:
            return None
        if not event.fwd[0].is_from_bot_me:
            return None
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

    def _get_user_msg(self, event: TgEvent) -> str:
        """
        Получение текста от пользователя
        """

        if event.message.command in self.full_names:
            return event.message.args_str_case
        else:
            return event.message.raw

    # PREPROMPT

    def _preprompt_works(self, args_slice_index: int, q: Q, is_for: str) -> ResponseMessageItem:
        """
        Обработка препромптов
        """

        q &= Q(provider=self.PREPROMPT_PROVIDER)

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

    @staticmethod
    def get_preprompt(sender: Profile, chat: Chat, provider) -> str | None:
        """
        Получить препромпт под текущую ситуацию (персональный в чате,в чате,в лс)
        """

        if chat:
            variants = [
                Q(author=sender, chat=chat, provider=provider),
                Q(author=None, chat=chat, provider=provider),
            ]
        else:
            variants = [
                Q(author=sender, chat=None, provider=provider),
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

    def _get_completions_rm(self, answer: str):
        """
        Пост-обработка сообщения в completions
        """

        answer = markdown_to_html(answer, self.bot)

        if len(answer) > self.bot.MAX_MESSAGE_TEXT_LENGTH:
            document = DocumentAttachment()
            document.parse(answer.encode('utf-8'), filename='answer.html')
            answer = "Твой запрос получился слишком большой. Положил ответ в файл"
            rmi = ResponseMessageItem(text=answer, attachments=[document], reply_to=self.event.message.id)
        else:
            rmi = ResponseMessageItem(text=answer, reply_to=self.event.message.id)
        return rmi

    def _get_draw_image_request_text(self):
        """
        Получение текста, который хочет нарисовать пользователь
        """

        if len(self.event.message.args) > 1:
            return " ".join(self.event.message.args_case[1:])
        elif self.event.message.quote:
            return self.event.message.quote
        elif self.event.fwd:
            return self.event.fwd[0].message.raw
        else:
            raise PWarning("Должен быть текст или пересланное сообщение")
