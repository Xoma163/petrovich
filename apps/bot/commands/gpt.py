import time

import openai
from django.core.cache import cache

from apps.bot.classes.command import Command
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.event.tg_event import TgEvent
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import replace_markdown_links, replace_markdown_bolds, replace_markdown_quotes, \
    replace_markdown_code
from petrovich.settings import env


class GPT(Command):
    name = "gpt"
    names = ["гпт", "chatgpt", "чатгпт"]
    name_tg = 'gpt'
    help_text = "чат GPT"
    help_texts = [
        "(фраза) - общение с ботом",
        "нарисуй (фраза) - генерация картинки",
    ]
    help_texts_extra = \
        "Если отвечать на сообщения бота через кнопку \"Ответить\" то будет продолжаться непрерывный диалог.\n" \
        "В кэше хранится только 1 час переписок"
    access = Role.TRUSTED
    args = 1

    def start(self) -> ResponseMessage:
        if self.event.message.args[0] == "нарисуй":
            return self.draw_image()
        return self.text_chat()

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

    def text_chat(self) -> ResponseMessage:
        openai.api_key = env.str("OPENAI_KEY")
        openai.api_base = "https://api.openai.com/v1"

        tries = 0
        response = None

        while not response and tries < 1:
            try:
                self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.TYPING)
                response = openai.ChatCompletion.create(
                    model='gpt-4',
                    messages=self.get_dialog()
                )
            except (openai.error.RateLimitError, openai.error.InvalidRequestError):
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
        answer = replace_markdown_links(answer, self.bot)
        answer = replace_markdown_bolds(answer, self.bot)
        answer = replace_markdown_quotes(answer, self.bot)
        answer = replace_markdown_code(answer, self.bot)
        return ResponseMessage(ResponseMessageItem(text=answer, reply_to=self.event.message.id))

    def get_dialog(self):
        data = cache.get(self.event.peer_id)
        if not self.event.fwd:
            return {'role': "user", 'content': self.event.message.args_str_case},
        reply_to_id = self.event.fwd[0].message.id
        history = []
        while True:
            raw = data.get(reply_to_id)
            tg_event = TgEvent({"message": raw}, self.bot)
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
        history.append({'role': "user", 'content': self.event.message.args_str_case})
        return history
