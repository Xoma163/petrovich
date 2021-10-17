from apps.bot.APIs.amazon.AmazonTranslateAPI import AmazonTranslateAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.utils import has_cyrillic


class Translate(Command):
    name = "перевод"
    names = ["переведи"]
    help_text = "автоматический переводчик"
    help_texts = [
        "(Текст/Пересылаемые сообщения) - в зависимости от текста переводит на нужный язык(английский или русский)"
    ]
    args_or_fwd = 1

    def start(self):
        fwd = self.event.fwd
        if not fwd:
            text = self.event.message.args_str
        else:
            text = ""
            for msg in fwd:
                if msg.message:
                    text += f"{msg.message.raw}\n"

        if not text:
            raise PWarning("Нет текста в сообщении или пересланных сообщениях")
        if has_cyrillic(text):
            lang = 'en'
        else:
            lang = 'ru'
        amazon_translate_api = AmazonTranslateAPI()
        return amazon_translate_api.get_translate(text, lang)
