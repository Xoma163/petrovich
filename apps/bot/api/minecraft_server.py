from mcstatus import JavaServer

from apps.bot.utils.do_the_linux_command import do_the_linux_command
from apps.bot.utils.utils import check_command_time


class MinecraftServer:

    def __init__(self, ip, port=25565, delay=None, names=None, map_url=None):
        self.ip = ip
        self.port = port

        self.delay = delay
        self.names = names
        self.map_url = map_url

        self.server_info = None

    def get_version(self):
        return self.names[0]

    def _get_service_name(self):
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
