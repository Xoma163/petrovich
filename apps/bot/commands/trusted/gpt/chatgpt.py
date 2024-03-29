import datetime
from typing import Optional

from django.db.models import Q, Sum

from apps.bot.api.gpt.chatgpt import ChatGPTAPI
from apps.bot.api.gpt.response import GPTAPIResponse
from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.command import Command
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Role, Platform
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.event.event import Event
from apps.bot.classes.event.tg_event import TgEvent
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.models import Profile, Chat
from apps.bot.utils.cache import MessagesCache
from apps.bot.utils.utils import markdown_to_html
from apps.service.models import GPTPrePrompt, GPTUsage
from petrovich.settings import env


class ChatGPT(Command):
    name = "gpt"
    names = ["гпт", "chatgpt", "чатгпт"]

    help_text = HelpText(
        commands_text="чат GPT",
        help_texts=[
            HelpTextItem(Role.TRUSTED, [
                HelpTextItemCommand("(фраза)", "общение с ботом"),
                HelpTextItemCommand("(пересланное сообщение)", "общение с ботом"),
                HelpTextItemCommand("(фраза) [картинка]", "общение с ботом с учётом пересланной картинки"),
                HelpTextItemCommand("нарисуй (фраза/пересланное сообщение)", "генерация картинки"),
                HelpTextItemCommand("препромпт [конфа]", "посмотреть текущий препромпт"),
                HelpTextItemCommand("препромпт [конфа] (текст)", "добавить препромпт"),
                HelpTextItemCommand("препромпт [конфа] удалить", "удаляет препромпт"),
                HelpTextItemCommand("стата", "статистика по использованию"),
            ])
        ],
        extra_text=(
            "Если отвечать на сообщения бота через кнопку \"Ответить\" то будет продолжаться непрерывный диалог.\n"
            "В таком случае необязательно писать команду, можно просто текст\n\n"
            "Порядок использования препромптов в конфах:\n"
            "1) Персональный препромт конфы\n"
            "2) Персональный препромт\n"
            "3) Препромпт конфы"
        )
    )

    access = Role.TRUSTED
    platforms = [Platform.TG]

    PREPROMPT_PROVIDER = GPTPrePrompt.CHATGPT

    def accept(self, event: Event):
        accept = super().accept(event)
        if accept:
            return True

        return bool(self.get_first_gpt_event_in_replies(event))

    def start(self) -> ResponseMessage:
        self.event: TgEvent
        if self.event.message.args:
            arg0 = self.event.message.args[0]
            if arg0 in ["нарисуй", "draw"]:
                return self.draw_image()
            elif arg0 in ["стата", "статистика", "stat"]:
                return self.statistics()
            elif arg0 in ["препромпт", "препромт", "промпт", "промт", "preprompt", "prepromp", "prompt", "promt"]:
                return self.preprompt()

        user_message = self.get_user_msg(self.event)
        messages = self.get_dialog(user_message)
        photos = self.event.get_all_attachments([PhotoAttachment])
        photos_data = []
        for photo in photos:
            base64 = photo.base64()
            photos_data.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64}"}})
        messages[-1]['content'] = [{"type": "text", "text": messages[-1]['content']}]
        messages[-1]['content'] += photos_data

        return self.text_chat(messages)

    def draw_image(self, model=None, use_stats=True) -> ResponseMessage:
        if model is None:
            model = ChatGPTAPI.DALLE_3

        if len(self.event.message.args) > 1:
            request_text = " ".join(self.event.message.args_case[1:])
        elif self.event.message.quote:
            request_text = self.event.message.quote
        elif self.event.fwd:
            request_text = self.event.fwd[0].message.raw
        else:
            raise PWarning("Должен быть текст или пересланное сообщение")
        chat_gpt_api = ChatGPTAPI(model, log_filter=self.event.log_filter)

        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_PHOTO, self.event.peer_id):
            response: GPTAPIResponse = chat_gpt_api.draw(request_text)

        if not response.images_url:
            raise PWarning("Не смог сгенерировать :(")

        attachments = []
        for image_url in response.images_url:
            att = self.bot.get_photo_attachment(image_url)
            att.download_content()
            attachments.append(att)

        answer = f'Результат генерации по запросу "{response.images_prompt}"'
        if use_stats:
            cost = chat_gpt_api.usage['image_cost'] * chat_gpt_api.usage['images_tokens']
            GPTUsage(
                author=self.event.sender,
                images_tokens=chat_gpt_api.usage['images_tokens'],
                cost=cost
            ).save()

        return ResponseMessage(
            ResponseMessageItem(text=answer, attachments=attachments, reply_to=self.event.message.id))

    def text_chat(self, messages, model=None, use_stats=True) -> ResponseMessage:
        if model is None:
            photos = self.event.get_all_attachments([PhotoAttachment])
            if photos:
                model = ChatGPTAPI.GPT_4_VISION
            else:
                model = ChatGPTAPI.GPT_4

        chat_gpt_api = ChatGPTAPI(model, log_filter=self.event.log_filter)

        with ChatActivity(self.bot, ActivitiesEnum.TYPING, self.event.peer_id):
            response: GPTAPIResponse = chat_gpt_api.completions(messages)

        answer = markdown_to_html(response.text, self.bot)
        if use_stats:
            cost = chat_gpt_api.usage['prompt_tokens'] * chat_gpt_api.usage['prompt_token_cost'] + \
                   chat_gpt_api.usage['completion_tokens'] * chat_gpt_api.usage['completion_token_cost']
            GPTUsage(
                author=self.event.sender,
                prompt_tokens=chat_gpt_api.usage['prompt_tokens'],
                completion_tokens=chat_gpt_api.usage['completion_tokens'],
                cost=cost
            ).save()

        return ResponseMessage(ResponseMessageItem(text=answer, reply_to=self.event.message.id))

    def get_dialog(self, user_message, use_preprompt=True) -> list:
        mc = MessagesCache(self.event.peer_id)
        data = mc.get_messages()
        preprompt = None
        if use_preprompt:
            preprompt = self.get_preprompt(self.event.sender, self.event.chat, self.PREPROMPT_PROVIDER)

        history = []
        if not self.event.fwd:
            if preprompt:
                history.append({"role": "system", "content": preprompt})
            history.append({'role': "user", 'content': user_message})
            return history

        reply_to_id = self.event.fwd[0].message.id
        history = []
        if first_event := self.get_first_gpt_event_in_replies(self.event):
            while True:
                raw = data.get(reply_to_id)
                tg_event = TgEvent({"message": raw})
                tg_event.setup_event()
                is_me = str(tg_event.from_id) == env.str("TG_BOT_GROUP_ID")
                if is_me:
                    history.append({'role': 'assistant', 'content': tg_event.message.raw})
                else:
                    msg = self.get_user_msg(tg_event)
                    history.append({'role': "user", 'content': msg})
                reply_to_id = data.get(reply_to_id, {}).get('reply_to_message', {}).get('message_id')
                if not reply_to_id or tg_event.message.id == first_event.message.id:
                    break
            if first_event.fwd:
                history.append({'role': "user", 'content': first_event.fwd[0].message.raw})
        else:
            history.append({'role': "user", 'content': self.event.fwd[0].message.raw})

        if preprompt:
            history.append({"role": "system", "content": preprompt})
        history = list(reversed(history))
        history.append({'role': "user", 'content': user_message})
        return history

    def get_first_gpt_event_in_replies(self, event) -> Optional[TgEvent]:
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

    def get_user_msg(self, event: TgEvent) -> str:
        if event.message.command in self.full_names:
            return event.message.args_str_case
        else:
            return event.message.raw

    def preprompt(self) -> ResponseMessage:
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

    def _preprompt_works(self, args_slice_index: int, q: Q, is_for: str) -> ResponseMessage:
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
        return ResponseMessage(rmi)

    @staticmethod
    def get_preprompt(sender: Profile, chat: Chat, provider) -> Optional[str]:
        variants = [
            Q(author=sender, chat=chat, provider=provider),
            Q(author=sender, chat=None, provider=provider),
            Q(author=None, chat=chat, provider=provider),
        ]

        for q in variants:
            try:
                return GPTPrePrompt.objects.get(q).text
            except GPTPrePrompt.DoesNotExist:
                continue
        return None

    def statistics(self) -> ResponseMessage:
        if self.event.is_from_chat:
            profiles = Profile.objects.filter(chats=self.event.chat)
            results = []
            for profile in profiles:
                if profile.pk in [92, 91]:
                    continue
                res = self._get_stat_for_user(profile)
                if res:
                    results.append(self._get_stat_for_user(profile))
            if not results:
                raise PWarning("Ещё не было использований GPT среди участников чата")
            answer = "\n\n".join(results)
        else:
            answer = self._get_stat_for_user(self.event.sender)
            if not answer:
                raise PWarning("Ещё не было использований GPT")

        return ResponseMessage(ResponseMessageItem(answer))

    def _get_stat_for_user(self, profile: Profile) -> Optional[str]:
        stats_all = self._get_stat_db_profile(Q(author=profile))
        if not stats_all:
            return None
        dt_now = datetime.datetime.now()
        stats_today = self._get_stat_db_profile(Q(author=profile, created_at__gte=dt_now - datetime.timedelta(days=1)))
        stats_week = self._get_stat_db_profile(Q(author=profile, created_at__gte=dt_now - datetime.timedelta(days=7)))
        stats_month = self._get_stat_db_profile(Q(author=profile, created_at__gte=dt_now - datetime.timedelta(days=30)))

        return f"{profile}:\n" \
               f"Сегодня - $ {round(stats_today, 2)}\n" \
               f"Неделя - $ {round(stats_week, 2)}\n" \
               f"Месяц - $ {round(stats_month, 2)}\n" \
               f"Всего - $ {round(stats_all, 2)}\n"

    @staticmethod
    def _get_stat_db_profile(q):
        res = GPTUsage.objects.filter(q).aggregate(Sum('cost')).get('cost__sum')
        return res if res else 0
