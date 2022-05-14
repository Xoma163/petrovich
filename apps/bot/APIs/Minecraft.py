import json
import threading
import time
from datetime import datetime

import requests
from mcrcon import MCRcon

from apps.bot.classes.bots.Bot import get_bot_by_platform
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.models import Profile
from apps.bot.utils.DoTheLinuxComand import do_the_linux_command
from apps.bot.utils.utils import remove_tz, check_command_time
from apps.service.models import Service
from petrovich.settings import env, BASE_DIR, MAIN_DOMAIN


class MinecraftAPI:

    def __init__(self, ip, port=25565, amazon=False, event=None, delay=None, names=None, map_url=None, auto_off=False):
        self.ip = ip
        self.port = port
        self.amazon = amazon
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

    # ToDo: hardcode
    @staticmethod
    def check_amazon_server_status():
        url = env.str("MINECRAFT_1_12_2_STATUS_URL")
        response = requests.get(url).json()
        return response['InstanceState']['Name'] == 'running'

    def _prepare_message(self, action):
        translator = {
            'start': 'Стартуем',
            'stop': "Финишируем"
        }

        return f"{translator[action]} майн {self.get_version()}!" \
               f"\nИнициатор - {self.event.sender}"

    def _start_local(self):
        do_the_linux_command(f'sudo systemctl start {self._get_service_name()}')

    # ToDo: hardcode
    @staticmethod
    def _start_amazon():
        url = env.str("MINECRAFT_1_12_2_START_URL")
        url_status = env.str("MINECRAFT_1_12_2_STATUS_URL")
        response = requests.get(url_status).json()
        if response['InstanceState']['Name'] == 'stopped':
            requests.post(url)
        else:
            raise PWarning(
                f"Сервер сейчас имеет состояние {response['InstanceState']['Name']}, не могу запустить")

    def start(self, send_notify=True):
        check_command_time(self._get_service_name(), self.delay)

        if self.amazon:
            self._start_amazon()
        else:
            self._start_local()

        if send_notify:
            message = self._prepare_message("start")
            self.send_notify_thread(message)

    def _stop_local(self):
        do_the_linux_command(f'sudo systemctl stop {self._get_service_name()}')

    def _stop_amazon(self):
        if not self.check_amazon_server_status():
            return False
        self.send_rcon('/stop')
        while True:
            server_is_offline = not self.send_rcon('/help')
            if server_is_offline:
                break
            time.sleep(5)

        url = env.str("MINECRAFT_1_12_2_STOP_URL")
        requests.post(url)
        Service.objects.filter(name=f'stop_{self._get_service_name()}').delete()
        return True

    def stop(self, send_notify=True):
        check_command_time(self._get_service_name(), self.delay)

        if self.amazon:
            self._stop_amazon()
        else:
            self._stop_local()
        if send_notify:
            message = self._prepare_message("stop")
            self.send_notify_thread(message)

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

    def send_notify_thread(self, message):
        """
        Не задерживаем вывод ответа от Петровича при старте/стопе сервера
        """

        def send_notify():

            users_notify = Profile.objects.filter(groups__name=Role.MINECRAFT_NOTIFY.name)
            if self.event:
                users_notify = users_notify.exclude(id=self.event.sender.id)
                if self.event.chat:
                    users_in_chat = self.event.chat.users.all()
                    users_notify = users_notify.exclude(pk__in=users_in_chat)
            for user in users_notify:
                bot = get_bot_by_platform(user.get_platform_enum())
                bot.parse_and_send_msgs_thread(message, user.user_id)

        thread = threading.Thread(target=send_notify)
        thread.start()

    def stop_if_need(self):
        if not self.auto_off:
            return
        self.get_server_info()
        # Если сервак онлайн и нет игроков
        if self.server_info['online'] and not self.server_info['players']:
            obj, created = Service.objects.get_or_create(name=f'stop_{self._get_service_name()}')

            # Создание событие. Уведомление, что мы скоро всё отрубим
            if created:
                message = f"Если никто не зайдёт на сервак по майну {self.get_version()}, то через полчаса я его остановлю"
                users_notify = Profile.objects.filter(groups__name=Role.MINECRAFT_NOTIFY.name)
                for user in users_notify:
                    bot = get_bot_by_platform(user.get_platform_enum())
                    bot.parse_and_send_msgs_thread(message, user.user_id)

            # Если событие уже было создано, значит пора отрубать
            else:
                update_datetime = obj.update_datetime
                delta_seconds = (datetime.utcnow() - remove_tz(update_datetime)).seconds
                if delta_seconds <= 1800 + 100:
                    obj.delete()
                    Service.objects.get_or_create(self._get_service_name())

                    self.stop(send_notify=False)

                    message = f"Вырубаю майн {self.get_version()}"
                    users_notify = Profile.objects.filter(groups__name=Role.MINECRAFT_NOTIFY.name)
                    for user in users_notify:
                        bot = get_bot_by_platform(user.get_platform_enum())
                        bot.parse_and_send_msgs_thread(message, user.user_id)
                else:
                    obj.delete()

        # Эта ветка нужна, чтобы вручную вырубленные серверы не провоцировали при последующем старте отключение в 0/30 минут
        else:
            Service.objects.filter(name=f'stop_{self._get_service_name()}').delete()


minecraft_servers = [
    MinecraftAPI(
        **{
            'ip': MAIN_DOMAIN,
            'port': 25565,
            'amazon': False,
            'event': None,
            'delay': 60,
            'names': ['1.12.2', "1.12"],
            'map_url': f"http://{MAIN_DOMAIN}:8123/?worldname=WTTF#",
            'auto_off': False
        }),
]


def get_minecraft_version_by_args(version):
    if version is None:
        return minecraft_servers[0]
    for minecraft_server in minecraft_servers:
        if version in minecraft_server.names:
            return minecraft_server
    raise PWarning("Я не знаю такой версии")
