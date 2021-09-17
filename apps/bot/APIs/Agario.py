from apps.bot.classes.DoTheLinuxComand import do_the_linux_command, is_systemd_service_active
from apps.bot.classes.Exceptions import PWarning


class AgarioAPI:
    def __init__(self, version):
        self.version = version

    def _get_service_name(self):
        return f"agario-server-{self.version}"

    @staticmethod
    def get_url():
        return "http://agario.edubovit.net"

    def start(self):
        do_the_linux_command(f'sudo systemctl start {self._get_service_name()}')

    def stop(self):
        do_the_linux_command(f'sudo systemctl stop {self._get_service_name()}')

    def get_server_info(self):
        active = is_systemd_service_active(self._get_service_name())
        if active:
            result = f"Агарио {self.version} запущен ✅ - {self.get_url()}\n"
        else:
            result = f"Агарио {self.version} остановлен ⛔"

        return result


agario_servers = [
    AgarioAPI(
        **{
            'version': 1
        }),
    AgarioAPI(
        **{
            'version': 2
        }),
    AgarioAPI(
        **{
            'version': 3
        }),
]


def get_agario_version_by_args(version):
    if version is None:
        return agario_servers[0]
    for agario_server in agario_servers:
        if version == str(agario_server.version):
            return agario_server
    raise PWarning("Я не знаю такой версии")
