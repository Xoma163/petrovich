from apps.bot.classes.const.exceptions import PError
from apps.bot.commands.minecraft.server_data import MinecraftServerData, MinecraftServerStatus
from apps.bot.utils.do_the_linux_command import do_the_linux_command
from apps.bot.utils.utils import check_command_time


class MinecraftServer:
    DEFAULT_PORT = 25565

    def __init__(
            self, ip: str, port: int | None = None, delay: int | None = None, names: list[str] = None,
            map_url: str = None,
            service_name: str = None
    ):
        self.ip: str = ip
        if port is None:
            port = self.DEFAULT_PORT
        self.port: int = port

        self.delay: int = delay
        self.names: list[str] = names if names else []
        self.map_url: str = map_url
        self.service_name: str = service_name

        self.server_info: MinecraftServerData | None = None

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
        minecraft_server_status = MinecraftServerStatus(self.ip, self.port)
        try:
            self.server_info = minecraft_server_status.get_server_data()
        # ToDo: check
        except TimeoutError:
            self.server_info = MinecraftServerData()
            self.server_info.online = False
        except Exception:
            raise PError("Не смог получить данные по серверу")
        return self.server_info
