from typing import Optional

from apps.bot.api.gpt.chatgpt import ChatGPTAPI
from apps.bot.classes.command import Command
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Role, Platform
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.event.event import Event
from apps.bot.classes.event.tg_event import TgEvent
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.cache import MessagesCache
from apps.bot.utils.utils import replace_markdown
from petrovich.settings import env


class ChatGPT(Command):
    name = "gpt"
    names = ["гпт", "chatgpt", "чатгпт"]

    help_text = "чат GPT"
    help_texts = [
        "(фраза/пересланное сообщение) - общение с ботом",
        "(фраза) [картинка] - общение с ботом с учётом пересланной картинки",
        "нарисуй (фраза/пересланное сообщение) - генерация картинки",
    ]
    help_texts_extra = \
        "Если отвечать на сообщения бота через кнопку \"Ответить\" то будет продолжаться непрерывный диалог.\n" \
        "В таком случае необязательно писать команду, можно просто текст\n\n"
    access = Role.TRUSTED
    platforms = [Platform.TG]

    def accept(self, event: Event):
        accept = super().accept(event)
        if accept:
            return True

        return bool(self.get_first_gpt_event_in_replies(event))

    def start(self) -> ResponseMessage:
        if self.event.message.args and self.event.message.args[0] == "нарисуй":
            return self.draw_image()

        self.event: TgEvent
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

    def draw_image(self, model=None) -> ResponseMessage:
        if model is None:
            model = ChatGPTAPI.DALLE_3

        if len(self.event.message.args) > 1:
            request_text = " ".join(self.event.message.args_case[1:])
        elif self.event.fwd:
            request_text = self.event.fwd[0].message.raw
        else:
            raise PWarning("Должен быть текст или пересланное сообщение")
        chat_gpt_api = ChatGPTAPI(model)

        try:
            self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.UPLOAD_PHOTO)
            images = chat_gpt_api.draw(request_text)
        finally:
            self.bot.stop_activity_thread()

        if not images:
            raise PWarning("Не смог сгенерировать :(")

        real_prompt = images[0][1]
        attachments = []
        for image in images:
            url = image[0]
            att = self.bot.get_photo_attachment(url)
            att.download_content()
            att.public_download_url = None
            attachments.append(att)

        answer = f'Результат генерации по запросу "{real_prompt}"'
        return ResponseMessage(
            ResponseMessageItem(text=answer, attachments=attachments, reply_to=self.event.message.id))

    def text_chat(self, messages, model=None) -> ResponseMessage:
        if model is None:
            photos = self.event.get_all_attachments([PhotoAttachment])
            if photos:
                model = ChatGPTAPI.GPT_4_VISION
            else:
                model = ChatGPTAPI.GPT_4

        chat_gpt_api = ChatGPTAPI(model)

        try:
            self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.TYPING)
            answer = chat_gpt_api.completions(messages)
        finally:
            self.bot.stop_activity_thread()

        answer = answer \
            .replace(">", "&gt;") \
            .replace("<", "&lt;") \
            .replace("&lt;pre&gt;", "<pre>") \
            .replace("&lt;/pre&gt;", "</pre>")
        answer = replace_markdown(answer, self.bot)
        return ResponseMessage(ResponseMessageItem(text=answer, reply_to=self.event.message.id))

    def get_dialog(self, user_message, use_preprompt=True):
        mc = MessagesCache(self.event.peer_id)
        data = mc.get_messages()
        preprompt = None
        if use_preprompt:
            if self.event.sender.gpt_preprompt:
                preprompt = self.event.sender.gpt_preprompt
            elif self.event.chat and self.event.chat.gpt_preprompt:
                preprompt = self.event.chat.gpt_preprompt

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

    def get_user_msg(self, event: TgEvent):
        if event.message.command in self.full_names:
            return event.message.args_str_case
        else:
            return event.message.raw
