import re

import openai

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.consts.Exceptions import PWarning
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

    def start(self):
        if self.event.message.args[0] == "нарисуй":
            return self.draw_image()
        return self.text_chat()

    def draw_image(self):
        openai.api_key = env.str("CHIMERA_SECRET_KEY")
        openai.api_base = "https://chimeragpt.adventblocks.cc/api/v1"

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
        return {'text': f'Результат генерации по запросу "{request_text}"', 'attachments': attachments,
                'reply_to': self.event.message.id}

    def text_chat(self):
        request_text = self.event.message.args_str_case

        openai.api_key = env.str("CHIMERA_SECRET_KEY")
        openai.api_base = "https://chimeragpt.adventblocks.cc/api/v1"
        try:
            self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.TYPING)
            response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo-16k',
                messages=[
                    {'role': 'user', 'content': request_text},
                ],
                allow_fallback=True
            )
        except openai.error.APIError:
            raise PWarning("Какая-то непредвиденная ошибка. Попробуйте ещё раз")
        finally:
            self.bot.stop_activity_thread()
        result = response.choices[0].message.content
        result = self.replace_specsymbols_to_tg_format(result)
        return {'text': result, 'reply_to': self.event.message.id}

    def replace_specsymbols_to_tg_format(self, text):
        p = re.compile(r'\*\*(.*)\*\*')  # markdown bold
        for item in reversed(list(p.finditer(text))):
            start_pos = item.start()
            end_pos = item.end()
            bold_text = text[item.regs[1][0]:item.regs[1][1]]
            tg_bold_text = self.bot.get_bold_text(bold_text).replace("**", '')
            text = text[:start_pos] + tg_bold_text + text[end_pos:]
        return text
