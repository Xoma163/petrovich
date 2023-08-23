from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.messages.ResponseMessage import ResponseMessageItem, ResponseMessage


class Discord(Command):
    name = "дискорд"
    names = ["диск"]
    name_tg = 'discord'

    help_text = "ссылка на канал в дискорде"

    access = Role.TRUSTED

    def start(self) -> ResponseMessage:
        url = 'https://discord.gg/kYGSNzv'
        answer = self.bot.get_formatted_url("Дискорд", url)
        return ResponseMessage(ResponseMessageItem(text=answer))
