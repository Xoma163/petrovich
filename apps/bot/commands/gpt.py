import time

import openai

from apps.bot.classes.command import Command
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
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
        "нарисуй - генерация картинки",
    ]
    access = Role.TRUSTED
    args = 1

    MAX_TRIES = 5

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
        request_text = self.event.message.args_str_case

        openai.api_key = env.str("OPENAI_KEY")
        openai.api_base = "https://api.openai.com/v1"

        tries = 0
        response = None

        while not response and tries < 1:
            try:
                self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.TYPING)
                response = openai.ChatCompletion.create(
                    model='gpt-4',
                    messages=[
                        {'role': 'user', 'content': request_text},
                    ]
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
