from apps.birds.CameraHandler import CameraHandler
from apps.bot.APIs.Agario import get_agario_version_by_args
from apps.bot.APIs.Minecraft import get_minecraft_version_by_args
from apps.bot.APIs.Terraria import terraria_servers
from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand

cameraHandler = CameraHandler()


class Stop(CommonCommand):
    name = "стоп"
    help_text = "останавливает работу бота или модуля"
    help_texts = [
        "[сервис=бот [версия]] - останавливает сервис\n"
        "Сервис - бот/камера/майнкрафт/террария\n"
        "Если майнкрафт, то может быть указана версия, 1.12.2\n"
        "Если агарио, то может быть указана версия, 1, 2, 3\n"
    ]
    access = Role.TRUSTED

    def start(self):
        if self.event.args:
            arg0 = self.event.args[0].lower()
        else:
            arg0 = None

        menu = [
            [["камера"], self.menu_camera],
            [["майн", "майнкрафт", "mine", "minecraft"], self.menu_minecraft],
            [['террария', 'terraria'], self.menu_terraria],
            [['агарио', 'agario'], self.menu_agario],
            [['бот', 'bot'], self.menu_bot],
            [['default'], self.menu_bot]
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    def menu_camera(self):
        self.check_sender(Role.ADMIN)
        if cameraHandler.is_active():
            cameraHandler.terminate()
            return "Финишируем камеру"
        else:
            return "Камера уже финишировала"

    def menu_minecraft(self):
        self.check_sender(Role.MINECRAFT)
        version = self.event.args[1] if len(self.event.args) > 1 else None
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

    def menu_agario(self):
        version = self.event.args[1] if len(self.event.args) > 1 else None
        agario_server = get_agario_version_by_args(version)
        version = agario_server.version
        agario_server.stop()
        return f"Финишируем агарию {version}!"

    def menu_bot(self):
        self.check_sender(Role.ADMIN)
        self.bot.BOT_CAN_WORK = False
        cameraHandler.terminate()
        return "Финишируем"
