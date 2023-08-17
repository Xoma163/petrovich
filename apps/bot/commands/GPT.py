import re

import openai

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.classes.messages.ResponseMessage import ResponseMessageItem
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
            response = openai.Image.create(
                prompt=request_text,
                n=5,  # images count
                size="1024x1024"
            )
        except openai.error.APIError:
            raise PWarning("Какая-то непредвиденная ошибка. Попробуйте ещё раз")

        attachments = [self.bot.get_photo_attachment(x['url']) for x in response["data"]]
        return {'text': f'Результат генерации по запросу "{request_text}"', 'attachments': attachments,
                'reply_to': self.event.message.id}

    def text_chat(self):
        request_text = self.event.message.args_str_case

        openai.api_key = env.str("CHIMERA_SECRET_KEY")
        openai.api_base = "https://chimeragpt.adventblocks.cc/api/v1"
        try:
            response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo-16k',
                messages=[
                    {'role': 'user', 'content': request_text},
                ],
                stream=True,
                allow_fallback=True
            )
        except openai.error.APIError:
            raise PWarning("Какая-то непредвиденная ошибка. Попробуйте ещё раз")

        result = ""
        update_per_symbols = 100
        counter = update_per_symbols
        message_id = None

        for chunk in response:
            result += chunk.choices[0].delta.get("content", "")
            if len(result) > counter:
                if message_id is None:
                    message_id = self.send_message(result)
                else:
                    self.update_message(result, message_id)
                counter += update_per_symbols

        result = self.replace_specsymbols_to_tg_format(result)
        return {'text': result, 'message_id': message_id}

    def replace_specsymbols_to_tg_format(self, text):
        p = re.compile(r'\*\*(.*)\*\*')  # markdown bold
        for item in reversed(list(p.finditer(text))):
            start_pos = item.start()
            end_pos = item.end()
            bold_text = text[item.regs[1][0]:item.regs[1][1]]
            tg_bold_text = self.bot.get_bold_text(bold_text).replace("**", '')
            text = text[:start_pos] + tg_bold_text + text[end_pos:]
        return text

    def send_message(self, msg):
        rm = ResponseMessageItem(msg, self.event.peer_id, self.event.message_thread_id)
        rm.reply_to = self.event.message.id
        r = self.bot.send_response_message_item(rm)
        message_id = r.json()['result']['message_id']
        return message_id

    def update_message(self, msg, message_id):
        rm = ResponseMessageItem(msg, self.event.peer_id, self.event.message_thread_id)
        rm.message_id = message_id
        self.bot.send_response_message_item(rm)
