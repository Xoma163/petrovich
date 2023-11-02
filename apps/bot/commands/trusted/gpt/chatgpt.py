import re
import time
from typing import Optional

import openai

from apps.bot.classes.command import Command
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Role, Platform
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.event.event import Event
from apps.bot.classes.event.tg_event import TgEvent
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
        "нарисуй (фраза) - генерация картинки",
    ]
    help_texts_extra = \
        "Если отвечать на сообщения бота через кнопку \"Ответить\" то будет продолжаться непрерывный диалог.\n" \
        "В таком случае необязательно писать команду, можно просто текст"
    access = Role.TRUSTED
    platforms = [Platform.TG]

    GPT_4 = 'gpt-4'
    GPT_3 = 'gpt-3.5-turbo-16k-0613'

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

        return self.text_chat(messages)

    def draw_image(self) -> ResponseMessage:
        openai.api_key = env.str("OPENAI_KEY")
        openai.api_base = "https://api.openai.com/v1"

        request_text = " ".join(self.event.message.args_case[1:])
        try:
            self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.UPLOAD_PHOTO)
            response = openai.Image.create(
                prompt=request_text,
                n=5,  # images count
                size="1024x1024"
            )
        except openai.error.APIError:
            raise PWarning("Какая-то непредвиденная ошибка. Попробуйте ещё раз")
        finally:
            self.bot.stop_activity_thread()

        attachments = [self.bot.get_photo_attachment(x['url']) for x in response["data"]]
        answer = f'Результат генерации по запросу "{request_text}"'
        return ResponseMessage(
            ResponseMessageItem(text=answer, attachments=attachments, reply_to=self.event.message.id))

    def text_chat(self, messages, model=None) -> ResponseMessage:
        if model is None:
            model = self.GPT_4
        openai.api_key = env.str("OPENAI_KEY")
        openai.api_base = "https://api.openai.com/v1"

        tries = 0
        response = None

        while not response and tries < 1:
            try:
                self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.TYPING)
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages
                )
            except (openai.error.RateLimitError, openai.error.InvalidRequestError) as e:
                if e.user_message.startswith("Rate limit reached"):
                    raise PWarning("Ограничение на количество токенов.")
                elif e.user_message.startswith("This model's maximum context length"):
                    r = r"This model's maximum context length is (.*) tokens. However, your messages resulted in (.*) tokens. Please reduce the length of the messages."
                    re.findall(r, e.user_message)
                    k = round(int(re.findall(r, e.user_message)[0][1]) / int(re.findall(r, e.user_message)[0][0]), 2)
                    raise PWarning(f"Ограничение на количество токенов. Уменьшите запрос в {k} раз")
                time.sleep(5)
            except openai.error.APIError:
                time.sleep(2)
            except openai.error.PermissionError:
                raise PWarning("Не смогу дать ответ на этот запрос")
            finally:
                tries += 1
                self.bot.stop_activity_thread()
        if not response:
            raise PWarning("Какая-то непредвиденная ошибка. Попробуйте ещё раз")

        answer = response.choices[0].message.content
        answer = answer.replace(">", "&gt;").replace("<", "&lt;").replace("&lt;pre&gt;", "<pre>").replace(
            "&lt;/pre&gt;", "</pre>")
        answer = replace_markdown(answer, self.bot)
        return ResponseMessage(ResponseMessageItem(text=answer, reply_to=self.event.message.id))

    @staticmethod
    def get_dialog(event: TgEvent, user_message):
        mc = MessagesCache(event.peer_id)
        data = mc.get_messages()
        if not event.fwd:
            return [{'role': "user", 'content': event.message.args_str_case}]
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
        history = list(reversed(history))
        history.append({'role': "user", 'content': user_message})
        return history

    @staticmethod
    def get_first_event_in_replies(event) -> Optional[TgEvent]:
        mc = MessagesCache(event.peer_id)
        data = mc.get_messages()
        if not event.fwd:
            return None
        reply_to_id = event.fwd[0].message.id
        while True:
            raw = data.get(reply_to_id)
            tg_event = TgEvent({"message": raw})
            tg_event.setup_event()
            reply_to_id = data.get(reply_to_id, {}).get('reply_to_message', {}).get('message_id')
            if not reply_to_id:
                return tg_event
