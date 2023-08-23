from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem
from apps.bot.utils.DoTheLinuxComand import do_the_linux_command


class Linux(Command):
    name = "линукс"
    names = ["linux", "консоль", "терминал"]
    help_text = "запускает любую команду на сервере"
    help_texts = ["(команда) - запускает любую команду на сервере с уровнем прав server"]
    access = Role.ADMIN
    args = 1

    def start(self) -> ResponseMessage:
        answer = do_the_linux_command(self.event.message.args_str)
        return ResponseMessage(ResponseMessageItem(text=answer))
