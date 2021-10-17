from apps.birds.CameraHandler import CameraHandler
from apps.bot.APIs.Agario import get_agario_version_by_args
from apps.bot.APIs.Minecraft import get_minecraft_version_by_args
from apps.bot.APIs.Terraria import get_terraria_server_by_version
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role

cameraHandler = CameraHandler()


class Start(Command):
    name = "старт"
    help_text = "возобновляет работу бота или модуля"
    help_texts = [
        "(сервис=бот [версия]) - стартует сервис\n"
        "Сервис - камера/майнкрафт/террария\n"
        "Если майнкрафт, то может быть указана версия, 1.16.5\n"
        "Если агарио, то может быть указана версия, 1, 2, 3\n"
    ]
    access = Role.TRUSTED

    def start(self):
        if self.event.message.args:
            arg0 = self.event.message.args[0]
        else:
            arg0 = None

        menu = [
            [["камера"], self.menu_camera],
            [["майн", "майнкрафт", "mine", "minecraft"], self.menu_minecraft],
            [['террария', 'terraria'], self.menu_terraria],
            [['агарио', 'agario'], self.menu_agario]
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    def menu_camera(self):
        self.check_sender(Role.ADMIN)
        if not cameraHandler.is_active():
            cameraHandler.resume()
            return "Стартуем камеру!"
        else:
            return "Камера уже стартовала"

    def menu_minecraft(self):
        self.check_sender(Role.MINECRAFT)
        version = self.event.message.args[1] if len(self.event.message.args) > 1 else None
        minecraft_server = get_minecraft_version_by_args(version)
        version = minecraft_server.get_version()
        minecraft_server.event = self.event
        minecraft_server.start()

        message = f"Стартуем майн {version}"
        return message

    def menu_terraria(self):
        self.check_sender(Role.TERRARIA)
        terraria_server = get_terraria_server_by_version(None)
        terraria_server.start()
        return "Стартуем террарию!"

    def menu_agario(self):
        version = self.event.message.args[1] if len(self.event.message.args) > 1 else None
        agario_server = get_agario_version_by_args(version)
        version = agario_server.version
        agario_server.start()
        return f"Стартуем агарию {version}!"
