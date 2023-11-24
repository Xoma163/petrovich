from typing import Optional

from apps.bot.api.gpt.chatgpt import ChatGPTAPI
from apps.bot.classes.command import Command
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Role, Platform
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
        "(фраза) - общение с ботом",
        "(фраза) [картинка] - общение с ботом с учётом пересланной картинки",
        "нарисуй (фраза) - генерация картинки",
    ]
    help_texts_extra = \
        "Если отвечать на сообщения бота через кнопку \"Ответить\" то будет продолжаться непрерывный диалог.\n" \
        "В таком случае необязательно писать команду, можно просто текст"
    access = Role.TRUSTED
    platforms = [Platform.TG]

    def accept(self, event: Event):
        accept = super().accept(event)
        if accept:
            return True

        if first_event := self.get_first_event_in_replies(event):
            accept = super().accept(first_event)
            if accept:
                return True
        return False

    def start(self) -> ResponseMessage:
        if self.event.message.args and self.event.message.args[0] == "нарисуй":
            return self.draw_image()

        self.event: TgEvent
        if self.event.message.command in self.full_names:
            user_message = self.event.message.args_str_case
        else:
            user_message = self.event.message.raw

        messages = self.get_dialog(self.event, user_message)
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

        request_text = " ".join(self.event.message.args_case[1:])
        chat_gpt_api = ChatGPTAPI(model)

        try:
            self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.UPLOAD_PHOTO)
            images = chat_gpt_api.draw(request_text)
        finally:
            self.bot.stop_activity_thread()

        attachments = []
        for image in images:
            url = image[0]
            real_prompt = image[1]
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

    @staticmethod
    def get_dialog(event: TgEvent, user_message, use_preprompt=True):
        mc = MessagesCache(event.peer_id)
        data = mc.get_messages()

        preprompt = None
        if use_preprompt:
            if event.sender.gpt_preprompt:
                preprompt = event.sender.gpt_preprompt
            elif event.chat and event.chat.gpt_preprompt:
                preprompt = event.chat.gpt_preprompt

        if not event.fwd:
            history = []
            if preprompt:
                history.append({"role": "system", "content": preprompt})
            history.append({'role': "user", 'content': user_message})
            return history

        reply_to_id = event.fwd[0].message.id
        history = []
        while True:
            raw = data.get(reply_to_id)
            tg_event = TgEvent({"message": raw})
            tg_event.setup_event()
            is_me = str(tg_event.from_id) == env.str("TG_BOT_GROUP_ID")
            if is_me:
                history.append({'role': 'assistant', 'content': tg_event.message.raw})
            else:
                history.append({'role': "user", 'content': tg_event.message.args_str_case})
            reply_to_id = data.get(reply_to_id, {}).get('reply_to_message', {}).get('message_id')
            if not reply_to_id:
                break

        if preprompt:
            history.append({"role": "system", "content": preprompt})
        history = list(reversed(history))
        history.append({'role': "user", 'content': user_message})
        return history

    @staticmethod
    def get_first_event_in_replies(event) -> Optional[TgEvent]:
        mc = MessagesCache(event.peer_id)
        data = mc.get_messages()
        if not event.fwd:
            return None
        if not event.fwd[0].is_from_bot_me:
            return None
        reply_to_id = event.fwd[0].message.id
        while True:
            raw = data.get(reply_to_id)
            tg_event = TgEvent({"message": raw})
            tg_event.setup_event()
            reply_to_id = data.get(reply_to_id, {}).get('reply_to_message', {}).get('message_id')
            if not reply_to_id:
                return tg_event
