import transliterate

from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.classes.Command import Command
from apps.bot.utils.utils import has_cyrillic


def get_en_transliterate(msg):
    return transliterate.translit(msg, reversed=True)


def get_ru_transliterate(msg):
    return transliterate.translit(msg, 'ru')


class Transliteration(Command):
    name = "транслит"
    help_text = "автоматическая транслитерация"
    help_texts = [
        "(Текст/Пересланные сообщения) - в зависимости от фразы транслитит на нужный язык(английский или русский)"]
    args_or_fwd = 1

    def start(self):
        msgs = self.event.fwd
        if not msgs:
            msgs = [{'text': self.event.message.args_str, 'from_id': int(self.event.sender.user_id)}]
        translite_text = ""
        for msg in msgs:
            if msg['text']:
                text = msg['text']
                translite_text += f"{text}\n\n"

        if not translite_text:
            raise PWarning("Нет текста в сообщении или пересланных сообщениях")

        if has_cyrillic(translite_text):
            return get_en_transliterate(translite_text)
        else:
            return get_ru_transliterate(translite_text)
