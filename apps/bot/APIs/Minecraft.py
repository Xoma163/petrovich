import json
import time
from datetime import datetime

import requests
from mcrcon import MCRcon

from apps.bot.classes.Consts import Role
from apps.bot.classes.DoTheLinuxComand import do_the_linux_command
from apps.bot.classes.bots.CommonBot import get_bot_by_platform
from apps.bot.classes.common.CommonMethods import remove_tz
from apps.bot.models import Users
from apps.service.models import Service
from petrovich.settings import env, BASE_DIR, MAIN_DOMAIN


class MinecraftAPI:

    def __init__(self, version, ip=None, port=None, amazon=False, bot=None, event=None):
        self.version = version
        self.ip = ip
        self.port = port
        self.amazon = amazon
        self.event = event

        self.server_info = None

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

    @staticmethod
    def check_amazon_server_status():
        url = env.str("MINECRAFT_1_12_2_STATUS_URL")
        response = requests.get(url).json()
        return response['InstanceState']['Name'] == 'running'

    def _prepare_message(self, action):
        translator = {'start': 'Стартуем', 'stop': "Финишируем"}

        return f"{translator[action]} майн {self.version}!" \
               f"\nИнициатор - {self.event.sender}"

    def _start_local(self):
        do_the_linux_command(f'sudo systemctl start minecraft_{self.version}')

    @staticmethod
    def _start_amazon():
        url = env.str("MINECRAFT_1_12_2_START_URL")
        url_status = env.str("MINECRAFT_1_12_2_STATUS_URL")
        response = requests.get(url_status).json()
        if response['InstanceState']['Name'] == 'stopped':
            requests.post(url)
        else:
            raise RuntimeWarning(
                f"Сервер сейчас имеет состояние {response['InstanceState']['Name']}, не могу запустить")

    def start(self, send_notify=True):
        if self.amazon:
            self._start_amazon()
        else:
            self._start_local()

        if send_notify:
            message = self._prepare_message("start")
            self.send_notify(message)

    def _stop_local(self):
        do_the_linux_command(f'sudo systemctl stop minecraft_{self.version}')

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
        Service.objects.filter(name=f'stop_minecraft_{self.version}').delete()
        return True

    def stop(self, send_notify=True):
        if self.amazon:
            self._stop_amazon()
        else:
            self._stop_local()
        if send_notify:
            message = self._prepare_message("stop")
            self.send_notify(message)

    def get_server_info(self):
        command = f"{BASE_DIR}/venv/bin/mcstatus {self.ip}:{self.port} json"
        self.server_info = json.loads(do_the_linux_command(command))

    def parse_server_info(self):
        if not self.server_info['online']:
            result = f"Майн {self.version} - остановлен ⛔"
        else:
            players = " ".join(player['name'] for player in self.server_info['players'])
            result = f"Майн {self.server_info['version']} - запущен ✅ ({self.server_info['player_count']}/{self.server_info['player_max']}) - {self.ip}:{self.port}\n"
            if len(players) > 0:
                result += f"Игроки: {players}"
        return result

    def send_notify(self, message):
        users_notify = Users.objects.filter(groups__name=Role.MINECRAFT_NOTIFY.name)
        if self.event:
            users_notify = users_notify.exclude(id=self.event.sender.id)
            if self.event.chat:
                users_in_chat = self.event.chat.users_set.all()
                users_notify = users_notify.exclude(pk__in=users_in_chat)
        for user in users_notify:
            bot = get_bot_by_platform(user.get_platform_enum())()
            bot.parse_and_send_msgs_thread(user.user_id, message)

    def stop_if_need(self):
        self.get_server_info()
        # Если сервак онлайн и нет игроков
        if self.server_info['online'] and not self.server_info['players']:
            obj, created = Service.objects.get_or_create(name=f'stop_minecraft_{self.version}')

            # Создание событие. Уведомление, что мы скоро всё отрубим
            if created:
                message = f"Если никто не зайдёт на сервак по майну {self.version}, то через полчаса я его остановлю"
                users_notify = Users.objects.filter(groups__name=Role.MINECRAFT_NOTIFY.name)
                for user in users_notify:
                    bot = get_bot_by_platform(user.get_platform_enum())()
                    bot.parse_and_send_msgs_thread(user.user_id, message)

            # Если событие уже было создано, значит пора отрубать
            else:
                update_datetime = obj.update_datetime
                delta_seconds = (datetime.utcnow() - remove_tz(update_datetime)).seconds
                if delta_seconds <= 1800 + 100:
                    obj.delete()
                    Service.objects.get_or_create(name=f"minecraft_{self.version}")

                    self.stop(send_notify=False)

                    message = f"Вырубаю майн {self.version}"
                    users_notify = Users.objects.filter(groups__name=Role.MINECRAFT_NOTIFY.name)
                    for user in users_notify:
                        bot = get_bot_by_platform(user.get_platform_enum())()
                        bot.parse_and_send_msgs_thread(user.user_id, message)
                else:
                    obj.delete()

        # Эта ветка нужна, чтобы вручную вырубленные серверы не провоцировали при последующем старте отключение в 0/30 минут
        else:
            Service.objects.filter(name=f'stop_minecraft_{self.version}').delete()


# ToDo: чё за херня с серверами этими и снизу
servers_minecraft = [
    MinecraftAPI("1.12.2", MAIN_DOMAIN, 25565),
]


def get_minecraft_version_by_args(args):
    if args is None:
        args = "1.12.2"
    minecraft_versions = [
        # {'names': ['1.12.2', "1.12"], "delay": 30, "amazon": True},
        {'names': ['1.12.2', "1.12"], "delay": 60, "amazon": False},
        # {'names': ['1.12.2', "1.12"], "delay": 90, "amazon": False},
        # {'names': ['1.15.1', "1.15"], "delay": 90, "amazon": False}
    ]
    minecraft_server = None
    if len(args) == 1:
        minecraft_server = minecraft_versions[0]
    else:
        for minecraft_version in minecraft_versions:
            if args in minecraft_version['names']:
                minecraft_server = minecraft_version
                break
    return minecraft_server
