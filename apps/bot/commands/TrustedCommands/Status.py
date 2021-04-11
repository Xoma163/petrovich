from apps.bot.APIs.Agario import agario_servers
from apps.bot.APIs.Minecraft import minecraft_servers
from apps.bot.APIs.Terraria import terraria_servers
from apps.bot.classes.Consts import Role
from apps.bot.classes.DoTheLinuxComand import do_the_linux_command
from apps.bot.classes.common.CommonCommand import CommonCommand
from petrovich.settings import MAIN_DOMAIN


class Status(CommonCommand):
    name = "статус"
    help_text = "статус серверов по играм"
    access = Role.MINECRAFT

    def start(self):
        minecraft_result = ""
        for server in minecraft_servers:
            server.get_server_info()
            result = server.parse_server_info()
            minecraft_result += f"{result}\n\n"

        terraria_result = ""
        for server in terraria_servers:
            result = server.get_server_info()
            terraria_result += f"{result}\n\n"

        agario_result = ""
        for server in agario_servers:
            result = server.get_server_info()
            agario_result += f"{result}\n\n"

        total_str = f"{minecraft_result}" \
                    f"{terraria_result}" \
                    f"{agario_result}"

        return total_str


def get_terraria_server_info(port):
    command = "systemctl status terraria"
    response = do_the_linux_command(command)
    index1 = response.find("Active: ") + len("Active: ")
    index2 = response.find("(", index1) - 1
    status = response[index1:index2]
    if status == 'active':
        result = f"Террария запущена ✅ - {MAIN_DOMAIN}:{port}\n"
    else:
        result = "Террария остановлена ⛔"

    return result
