from apps.bot.APIs.Minecraft import get_minecraft_version_by_args
from apps.bot.APIs.Terraria import terraria_servers
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role


class Stop(Command):
    name = "стоп"

    help_text = "останавливает работу сервиса"
    help_texts = [
        "Сервис - камера/майнкрафт/террария",
        "Если майнкрафт, то может быть указана версия, 1.16.5"
    ]

    access = Role.TRUSTED
    args = 1

    def start(self):
        if self.event.message.args:
            arg0 = self.event.message.args[0]
        else:
            arg0 = None

        menu = [
            [["камера"], self.menu_camera],
            [["майн", "майнкрафт", "mine", "minecraft"], self.menu_minecraft],
            [['террария', 'terraria'], self.menu_terraria],
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    def menu_camera(self):
        self.check_sender(Role.ADMIN)
        from apps.bot.management.commands.start import camera_handler

        if camera_handler.is_active():
            camera_handler.terminate()
            return "Финишируем камеру"
        else:
            return "Камера уже финишировала"

    def menu_minecraft(self):
        self.check_sender(Role.MINECRAFT)
        version = self.event.message.args[1] if len(self.event.message.args) > 1 else None
        minecraft_server = get_minecraft_version_by_args(version)
        version = minecraft_server.get_version()
        minecraft_server.event = self.event
        minecraft_server.stop()

        message = f"Финишируем майн {version}"
        return message

    def menu_terraria(self):
        self.check_sender(Role.TERRARIA)
        terraria_server = terraria_servers[0]
        terraria_server.stop()
        return "Финишируем террарию!"
