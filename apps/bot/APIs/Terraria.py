from apps.bot.utils.DoTheLinuxComand import do_the_linux_command, is_systemd_service_active
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.utils import check_command_time
from petrovich.settings import MAIN_DOMAIN


class TerrariaAPI:
    def __init__(self, port, version):
        self.port = port
        self.version = version

    @staticmethod
    def _get_service_name():
        return "terraria"

    def get_url(self):
        return f"{MAIN_DOMAIN}:{self.port}"

    def start(self):
        check_command_time('terraria', 10)
        do_the_linux_command(f'sudo systemctl start {self._get_service_name()}')

    def stop(self):
        do_the_linux_command(f'sudo systemctl stop {self._get_service_name()}')

    def get_server_info(self):
        active = is_systemd_service_active(self._get_service_name())
        if active:
            result = f"Террария запущена ✅ - {self.get_url()}\n"
        else:
            result = "Террария остановлена ⛔"

        return result


terraria_servers = [
    TerrariaAPI(
        **{
            'version': 1,
            'port': 7777,
        }),
]


def get_terraria_server_by_version(version):
    if version is None:
        return terraria_servers[0]
    for terraria_server in terraria_servers:
        if version == str(terraria_server.version):
            return terraria_server
    raise PWarning("Я не знаю такой версии")
