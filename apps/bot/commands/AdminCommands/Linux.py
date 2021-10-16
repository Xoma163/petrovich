from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.utils.DoTheLinuxComand import do_the_linux_command


class Linux(Command):
    name = "линукс"
    names = ["linux", "консоль", "терминал"]
    help_text = "запускает любую команду на сервере"
    help_texts = ["(команда) - запускает любую команду на сервере с уровнем прав server"]
    access = Role.ADMIN
    args = 1

    def start(self):
        return do_the_linux_command(self.event.message.args_str)
