from apps.bot.api.minecraft_server import MinecraftServer
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from petrovich.settings import MAIN_DOMAIN


class Minecraft(Command):
    name = "майнкрафт"
    names = ["майн", "mine", "minecraft"]

    help_text = HelpText(
        commands_text="действия с сервером майнкрафта",
        help_texts=[
            HelpTextItem(Role.MINECRAFT, [
                "- статус по всем серверам",
                "старт [версия=1.20.1] - стартует сервер майнкрафта",
                "стоп [версия=1.20.1] - стопит сервер майнкрафта"
            ])
        ]
    )

    access = Role.MINECRAFT

    servers = [
        MinecraftServer(
            **{
                'ip': MAIN_DOMAIN,
                'port': 25565,
                'event': None,
                'delay': 60,
                'names': ['1.20.1', "1.20"],
                # 'map_url': f"http://{MAIN_DOMAIN}:8123/?worldname=world#",
            }
        ),
    ]

    def start(self) -> ResponseMessage:
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
        rmi = method()
        return ResponseMessage(rmi)

    def _get_minecraft_server_by_version(self, version):
        if version is None:
            return self.servers[0]
        for minecraft_server in self.servers:
            if version in minecraft_server.names:
                return minecraft_server
        raise PWarning("Я не знаю такой версии")

    def get_minecraft_server(self):
        version = self.event.message.args[1] if len(self.event.message.args) > 1 else None
        minecraft_server = self._get_minecraft_server_by_version(version)
        minecraft_server.event = self.event
        return minecraft_server

    def menu_start(self) -> ResponseMessageItem:
        self.check_args(1)
        minecraft_server = self.get_minecraft_server()
        minecraft_server.start()

        version = minecraft_server.get_version()
        answer = f"Стартуем майн {version}"
        return ResponseMessageItem(text=answer)

    def menu_stop(self) -> ResponseMessageItem:
        self.check_args(1)
        minecraft_server = self.get_minecraft_server()
        minecraft_server.stop()

        version = minecraft_server.get_version()
        answer = f"Финишируем майн {version}"
        return ResponseMessageItem(text=answer)

    def menu_status(self) -> ResponseMessageItem:
        minecraft_result = ""
        for server in self.servers:
            server.get_server_info()
            result = server.get_server_info_str()
            minecraft_result += f"{result}\n\n"

        answer = minecraft_result
        return ResponseMessageItem(text=answer)
