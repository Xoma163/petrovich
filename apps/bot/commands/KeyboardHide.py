from apps.bot.classes.Command import Command
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.consts.Consts import Platform


class KeyboardHide(Command):
    name = "скрыть"
    help_text = "убирает клавиатуру"

    platforms = [Platform.TG]

    bot: TgBot

    EMPTY_KEYBOARD_TG = {
        'remove_keyboard': True
    }

    def start(self):
        return {'keyboard': self.EMPTY_KEYBOARD_TG, 'text': "Скрыл"}
