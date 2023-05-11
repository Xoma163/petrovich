from apps.bot.APIs.MinecraftAPI import get_minecraft_version_by_args
from apps.bot.APIs.MinecraftAPI import minecraft_servers
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role


class Minecraft(Command):
    name = "майнкрафт"
    names = ["майн", "mine", "minecraft"]
    help_text = "действия с сервером майнкрафта"
    help_texts = [
        "- статус по всем серверам"
        "старт [версия=1.19.2] - стартует сервер майнкрафта"
        "стоп [версия=1.19.2] - стопит сервер майнкрафта"
    ]

    access = Role.MINECRAFT

    def start(self):
        if self.event.message.args:
            arg0 = self.event.message.args[0]
        else:
            arg0 = None

        menu = [
            [["старт"], self.menu_start],
            [["стоп"], self.menu_stop],
            [["статус"], self.menu_status],
            [['default'], self.menu_status]

        ]
        method = self.handle_menu(menu, arg0)
        return method()

    def get_minecraft_server(self):
        version = self.event.message.args[1] if len(self.event.message.args) > 1 else None
        minecraft_server = get_minecraft_version_by_args(version)
        minecraft_server.event = self.event
        return minecraft_server

    def menu_start(self):
        self.check_args(1)
        minecraft_server = self.get_minecraft_server()
        minecraft_server.start()

        version = minecraft_server.get_version()
        message = f"Стартуем майн {version}"
        return message

    def menu_stop(self):
        self.check_args(1)
        minecraft_server = self.get_minecraft_server()
        minecraft_server.stop()

        version = minecraft_server.get_version()
        message = f"Финишируем майн {version}"
        return message

    @staticmethod
    def menu_status():
        minecraft_result = ""
        for server in minecraft_servers:
            server.get_server_info()
            result = server.get_server_info_str()
            minecraft_result += f"{result}\n\n"

        return minecraft_result
