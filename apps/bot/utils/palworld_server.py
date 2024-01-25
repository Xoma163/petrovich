from apps.bot.utils.do_the_linux_command import do_the_linux_command
from apps.bot.utils.utils import check_command_time
from petrovich.settings import env, MAIN_DOMAIN


class PalworldServer:
    HOST = MAIN_DOMAIN
    PORT = 8211

    RCON_PORT = env.str("PALWORLD_RCON_PORT")
    RCON_PASSWORD = env.str("PALWORLD_RCON_PASSWORD")

    DELAY = 30

    def __init__(self):
        self.server_info = {
            'player_max': 32,
            'online': True,
            'players': [],
        }

    def start(self):
        check_command_time('palworld', self.DELAY)
        do_the_linux_command('sudo systemctl start palworld')

    def stop(self):
        check_command_time('palworld', self.DELAY)
        do_the_linux_command("sudo systemctl stop palworld")

    def get_server_info(self):
        try:
            players = [x.split(',')[0].replace("\x1b[0m", "") for x in self.do_rcon("ShowPlayers").split('\n')[2:-2]]
            self.server_info['players'] = players
        except:
            self.server_info['online'] = False
        return self.server_info

    def do_rcon(self, command):
        answer = do_the_linux_command(f"rcon-cli --port {self.RCON_PORT} --password {self.RCON_PASSWORD} {command}")
        if "Failed to connect to RCON" in answer:
            raise RuntimeError
        return answer
