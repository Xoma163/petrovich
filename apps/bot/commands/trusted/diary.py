from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Diary(Command):
    name = "ежедневник"
    help_text = "ссылка на ежедневник"
    access = Role.TRUSTED
    suggest_for_similar = False

    def start(self) -> ResponseMessage:
        url = 'https://diary.andrewsha.net/'
        answer = self.bot.get_formatted_url("Ежедневник", url)
        return ResponseMessage(ResponseMessageItem(text=answer))
