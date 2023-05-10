from apps.bot.APIs.MinecraftAPI import get_minecraft_version_by_args
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role


class Stop(Command):
    name = "стоп"

    help_text = "останавливает работу сервиса"
    help_texts = ["(сервис) - майнкрафт/террария"]
    help_texts_extra = "Если майнкрафт, то может быть указана версия (1.19.2)"

    access = Role.MINECRAFT
    args = 1

    def start(self):
        if self.event.message.args:
            arg0 = self.event.message.args[0]
        else:
            arg0 = None

        menu = [
            [["майн", "майнкрафт", "mine", "minecraft"], self.menu_minecraft]
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    def menu_minecraft(self):
        version = self.event.message.args[1] if len(self.event.message.args) > 1 else None
        minecraft_server = get_minecraft_version_by_args(version)
        version = minecraft_server.get_version()
        minecraft_server.event = self.event
        minecraft_server.stop()

        message = f"Финишируем майн {version}"
        return message
