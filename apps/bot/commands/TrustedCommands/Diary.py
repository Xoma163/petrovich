from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem


class Diary(Command):
    name = "ежедневник"
    help_text = "ссылка на ежедневник"
    access = Role.TRUSTED
    suggest_for_similar = False

    def start(self) -> ResponseMessage:
        url = 'https://diary.andrewsha.net/'
        answer = self.bot.get_formatted_url("Ежедневник", url)
        return ResponseMessage(ResponseMessageItem(text=answer))
