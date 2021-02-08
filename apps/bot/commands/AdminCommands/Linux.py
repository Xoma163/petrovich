from apps.bot.classes.Consts import Role
from apps.bot.classes.DoTheLinuxComand import do_the_linux_command
from apps.bot.classes.common.CommonCommand import CommonCommand


class Linux(CommonCommand):
    names = ["линукс", "linux", "консоль", "терминал"]
    help_text = "Линукс - запускает любую команду на сервере"
    detail_help_text = "Линукс (команда) - запускает любую команду на сервере с уровнем прав server"
    access = Role.ADMIN
    args = 1

    def start(self):
        return do_the_linux_command(self.event.original_args)
