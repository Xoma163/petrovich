from mcstatus import JavaServer

from apps.bot.utils.do_the_linux_command import do_the_linux_command
from apps.bot.utils.utils import check_command_time


class MinecraftServer:
    DEFAULT_PORT = 25565

    def __init__(self, ip, port=None, delay=None, names=None, map_url=None, service_name=None):
        self.ip = ip
        if port is None:
            port = self.DEFAULT_PORT
        self.port = port

        self.delay = delay
        self.names = names
        self.map_url = map_url
        self.service_name = service_name

        self.server_info = None

    def get_version(self):
        return self.names[0]

    def _get_service_name(self):
        if self.service_name:
            return self.service_name
        return f'minecraft_{self.get_version()}'

    def start(self):
        check_command_time(self._get_service_name(), self.delay)
        do_the_linux_command(f'sudo systemctl start {self._get_service_name()}')

    def stop(self):
        check_command_time(self._get_service_name(), self.delay)
        do_the_linux_command(f'sudo systemctl stop {self._get_service_name()}')

    def get_server_info(self):
        server = JavaServer.lookup(f"{self.ip}:{self.port}")
        try:
            status = server.status()
            self.server_info = {
                'version': status.version.name,
                'player_max': status.players.max,
                'online': True,
                'players': [x.name for x in status.players.sample] if status.players.sample else [],
            }
        except ConnectionRefusedError:
            self.server_info = {
                'online': False
            }
        return self.server_info
