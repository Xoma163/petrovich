from mcrcon import MCRcon
from mcstatus import JavaServer

from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.bot.utils.do_the_linux_command import do_the_linux_command
from apps.bot.utils.utils import check_command_time
from petrovich.settings import env, MAIN_DOMAIN


class Minecraft:

    def __init__(self, ip, port=25565, event=None, delay=None, names=None, map_url=None):
        self.ip = ip
        self.port = port
        self.event = event

        self.delay = delay
        self.names = names
        self.map_url = map_url

        self.server_info = None

    def get_version(self):
        return self.names[0]

    def _get_service_name(self):
        return f'minecraft_{self.get_version()}'

    # ToDo: hardcode
    @staticmethod
    def send_rcon(command):
        try:
            with MCRcon(
                    env.str("MINECRAFT_1_12_2_IP"),
                    env.str("MINECRAFT_1_12_2_RCON_PASSWORD")
            ) as mcr:
                resp = mcr.command(command)
                if resp:
                    return resp
                else:
                    return False
        except Exception:
            return False

    def _prepare_message(self, action) -> ResponseMessageItem:
        translator = {
            'start': 'Стартуем',
            'stop': "Финишируем"
        }

        answer = f"{translator[action]} майн {self.get_version()}!" \
                 f"\nИнициатор - {self.event.sender}"
        return ResponseMessageItem(text=answer)

    def _start_local(self):
        do_the_linux_command(f'sudo systemctl start {self._get_service_name()}')

    def start(self):
        check_command_time(self._get_service_name(), self.delay)
        self._start_local()

    def _stop_local(self):
        do_the_linux_command(f'sudo systemctl stop {self._get_service_name()}')

    def stop(self):
        check_command_time(self._get_service_name(), self.delay)
        self._stop_local()

    def get_server_info(self):
        server = JavaServer.lookup(f"{self.ip}:{self.port}")
        try:
            status = server.status()
            self.server_info = {
                'version': status.version.name,
                'player_max': status.players.max,
                'online': True,
                'players': [x.name for x in status.players.sample],
            }
        except ConnectionRefusedError:
            self.server_info = {
                'online': False
            }

    def get_server_info_str(self):
        if not self.server_info['online']:
            return f"Майн {self.get_version()} - остановлен ⛔"

        version = self.server_info['version']
        player_max = self.server_info['player_max']
        player_range = f"({len(self.server_info['players'])}/{player_max})"

        result = f"Майн {version} - запущен ✅ {player_range} - {self.ip}:{self.port}"

        players = self.server_info['players']
        if players:
            players.sort(key=str.lower)
            players_str = ", ".join(players)
            result += f"\nИгроки: {players_str}"
        if self.map_url:
            result += f"\nКарта - {self.map_url}"
        return result


minecraft_servers = [
    Minecraft(
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


def get_minecraft_version_by_args(version):
    if version is None:
        return minecraft_servers[0]
    for minecraft_server in minecraft_servers:
        if version in minecraft_server.names:
            return minecraft_server
    raise PWarning("Я не знаю такой версии")
