from apps.bot.APIs.YandexTranslateAPI import YandexTranslateAPI
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import has_cyrillic


class Translate(CommonCommand):
    def __init__(self):
        names = ["перевод", "переведи"]
        help_text = "Перевод - автоматический переводчик"
        detail_help_text = "Перевод (Текст/Пересылаемые сообщения) - в зависимости от текста переводит на нужный " \
                           "язык(английский или русский)"
        super().__init__(names, help_text, detail_help_text)

    def start(self):
        fwd = self.event.fwd
        if not fwd:
            if not self.event.original_args:
                return "Требуется аргументы или пересылаемые сообщения"

            text = self.event.original_args
        else:
            text = ""
            for msg in fwd:
                if msg['text']:
                    text += f"{msg['text']}\n"

        if not text:
            return "Нет текста в сообщении или пересланных сообщениях"
        if has_cyrillic(text):
            lang = 'ru-en'
        else:
            lang = 'en-ru'
        yandextranslate_api = YandexTranslateAPI()
        return yandextranslate_api.get_translate(lang, text)
