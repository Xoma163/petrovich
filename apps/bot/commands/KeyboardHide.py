from apps.bot.classes.Command import Command
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem


class KeyboardHide(Command):
    name = "скрыть"
    help_text = "убирает клавиатуру"

    platforms = [Platform.TG]

    bot: TgBot

    EMPTY_KEYBOARD_TG = {
        'remove_keyboard': True
    }

    def start(self) -> ResponseMessage:
        answer = "Скрыл"
        keyboard = {'keyboard': self.EMPTY_KEYBOARD_TG}
        return ResponseMessage(ResponseMessageItem(text=answer, keyboard=keyboard))
