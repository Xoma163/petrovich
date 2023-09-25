from apps.bot.classes.bots.tg import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Platform
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


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
