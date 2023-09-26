import json
from copy import copy

from mcrcon import MCRcon

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.models import Profile
from apps.bot.utils.do_the_linux_command import do_the_linux_command
from apps.bot.utils.utils import check_command_time
from petrovich.settings import env, BASE_DIR, MAIN_DOMAIN


class Minecraft:

    def __init__(self, ip, port=25565, event=None, delay=None, names=None, map_url=None, auto_off=False):
        self.ip = ip
        self.port = port
        self.event = event

        self.delay = delay
        self.names = names
        self.map_url = map_url

        self.server_info = None
        self.auto_off = auto_off

    def get_version(self):
        return self.names[0]

    def _get_service_name(self):
        return f'minecraft_{self.get_version()}'

    # ToDo: hardcode
    @staticmethod
    def send_rcon(command):
        try:
            with MCRcon(env.str("MINECRAFT_1_12_2_IP"),
                        env.str("MINECRAFT_1_12_2_RCON_PASSWORD")) as mcr:
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

    def start(self, send_notify=True):
        check_command_time(self._get_service_name(), self.delay)

        self._start_local()

        if send_notify:
            message = self._prepare_message("start")
            self.send_notify(message)

    def _stop_local(self):
        do_the_linux_command(f'sudo systemctl stop {self._get_service_name()}')

    def stop(self, send_notify=True):
        check_command_time(self._get_service_name(), self.delay)

        self._stop_local()
        if send_notify:
            message = self._prepare_message("stop")
            self.send_notify(message)

    # Only if online
    def parse_server_info(self):
        """
        Порой json метод не срабатывает и приходится парсить руками
        """
        command = f"{BASE_DIR}/venv/bin/mcstatus {self.ip}:{self.port} status"
        response = do_the_linux_command(command)
        response_lines = response.split('\n')

        players_range_start_phrase = 'players: '
        players_range_end_phrase = ' '

        players_range_start_pos = response_lines[2].find(players_range_start_phrase) + len(players_range_start_phrase)
        players_range_end_pos = response_lines[2].find(players_range_end_phrase, players_range_start_pos)
        players_range = response_lines[2][players_range_start_pos:players_range_end_pos]
        players_range_split = players_range.split('/')
        server_info = {
            'version': response_lines[0][
                       response_lines[0].find('version: v') + len('version: v'):response_lines[0].find('(') - 1],
            'player_count': int(players_range_split[0]),
            'player_max': int(players_range_split[1]),
            'online': True,
            'players': '',
        }
        players_list_pos = response_lines[2].find('[')
        if players_list_pos != -1:
            players_list = response_lines[2][players_list_pos:].replace("[\'", '').replace('\']', '').split(',')
            server_info['players'] = [{
                'name': x[:x.find(' ')]
            } for x in players_list]
        return server_info

    def get_server_info(self):
        command = f"{BASE_DIR}/venv/bin/mcstatus {self.ip}:{self.port} json"
        server_info_json = json.loads(do_the_linux_command(command))
        server_is_online = server_info_json['online']
        server_is_send_bad_response = 'player_count' not in server_info_json and 'players' not in server_info_json
        if server_is_online and server_is_send_bad_response:
            server_info_json = self.parse_server_info()
        self.server_info = server_info_json

    def get_server_info_str(self):
        if not self.server_info['online']:
            result = f"Майн {self.get_version()} - остановлен ⛔"
        else:

            version = self.server_info.get('version', self.names[0])

            player_count = self.server_info.get('player_count', 0)
            player_max = self.server_info.get('player_max', None)

            player_range = ''
            if player_max:
                player_range = f"({player_count}/{player_max})"

            result = f"Майн {version} - запущен ✅ {player_range} - {self.ip}:{self.port}"

            players = self.server_info.get('players', None)
            if players:
                players_list = [x['name'] for x in players]
                players_list.sort(key=str.lower)
                players_str = ", ".join(players_list)
                result += f"\nИгроки: {players_str}"
            if self.map_url:
                result += f"\nКарта - {self.map_url}"
        return result

    def send_notify(self, rmi: ResponseMessageItem):
        profiles_notify = Profile.objects.filter(groups__name=Role.MINECRAFT_NOTIFY.name)
        if self.event:
            profiles_notify = profiles_notify.exclude(id=self.event.sender.id)
            if self.event.chat:
                users_in_chat = self.event.chat.users.all()
                profiles_notify = profiles_notify.exclude(pk__in=users_in_chat)
        bot = TgBot()
        rm = ResponseMessage()
        for profile in profiles_notify:
            user = profile.get_tg_user()
            rmi_copy = copy(rmi)
            rmi_copy.peer_id = user.user_id
            rm.messages.append(rmi_copy)
        bot.send_response_message_thread(rm)


minecraft_servers = [
    Minecraft(
        **{
            'ip': MAIN_DOMAIN,
            'port': 25565,
            'event': None,
            'delay': 30,
            'names': ['1.19.2', "1.19"],
            # 'map_url': f"http://{MAIN_DOMAIN}:8123/?worldname=WTTF#",
            'auto_off': False
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
