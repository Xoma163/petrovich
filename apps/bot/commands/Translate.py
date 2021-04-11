from apps.bot.APIs.amazon.AmazonTranslateAPI import AmazonTranslateAPI
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import has_cyrillic


class Translate(CommonCommand):
    name = "перевод"
    names = ["переведи"]
    help_text = "автоматический переводчик"
    help_texts = [
        "(Текст/Пересылаемые сообщения) - в зависимости от текста переводит на нужный язык(английский или русский)"
    ]

    def start(self):
        fwd = self.event.fwd
        if not fwd:
            if not self.event.original_args:
                raise PWarning("Требуется аргументы или пересылаемые сообщения")

            text = self.event.original_args
        else:
            text = ""
            for msg in fwd:
                if msg['text']:
                    text += f"{msg['text']}\n"

        if not text:
            raise PWarning("Нет текста в сообщении или пересланных сообщениях")
        if has_cyrillic(text):
            lang = 'en'
        else:
            lang = 'ru'
        amazon_translate_api = AmazonTranslateAPI()
        return amazon_translate_api.get_translate(text, lang)
