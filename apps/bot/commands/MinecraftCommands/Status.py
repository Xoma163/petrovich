from apps.bot.APIs.MinecraftAPI import minecraft_servers
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role


class Status(Command):
    name = "статус"
    name_tg = 'status'

    help_text = "статус серверов по играм"
    access = Role.MINECRAFT

    def start(self):
        minecraft_result = ""
        for server in minecraft_servers:
            server.get_server_info()
            result = server.get_server_info_str()
            minecraft_result += f"{result}\n\n"

        return minecraft_result
