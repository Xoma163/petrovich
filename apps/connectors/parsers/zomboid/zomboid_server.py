import dataclasses
import logging
import re
import subprocess

from apps.shared.exceptions import PWarning


logger = logging.getLogger("bot")


@dataclasses.dataclass
class ZomboidServerData:
    players_online: int | None = None
    players: list[str] = dataclasses.field(default_factory=list)
    raw_status: str = ""


class ZomboidServer:
    COMMAND_TIMEOUT = 300
    RESTART_COMMAND = ["sudo", "/usr/local/sbin/zomboid-restart-if-empty-updates", "--force"]
    FORCE_RESTART_COMMAND = ["sudo", "systemctl", "restart", "zomboid"]
    STATUS_COMMAND = ["sudo", "-u", "zomboid", "-H", "bash", "-lc", "cd /opt/zomboid && ./pzserver send players"]

    def __init__(self, log_filter: dict | None = None):
        self.log_filter = log_filter

    def restart(self) -> str:
        return self._run_command(self.RESTART_COMMAND, "Не смог перезапустить Zomboid")

    def force_restart(self) -> str:
        return self._run_command(self.FORCE_RESTART_COMMAND, "Не смог форсированно перезапустить Zomboid")

    def get_server_info(self) -> ZomboidServerData:
        output = self._run_command(self.STATUS_COMMAND, "Не смог получить статус Zomboid")
        return self.parse_players(output)

    @classmethod
    def parse_players(cls, output: str) -> ZomboidServerData:
        players_online = None
        players = []

        if match := re.search(r"Players connected\s*\((\d+)\):", output):
            players_online = int(match.group(1))

        for line in output.splitlines():
            line = line.strip()
            if line.startswith("-"):
                player = line[1:].strip()
                if player:
                    players.append(player)

        if players_online is None and players:
            players_online = len(players)

        return ZomboidServerData(players_online=players_online, players=players, raw_status=output.strip())

    def _run_command(self, command: list[str], error_message: str) -> str:
        try:
            process = subprocess.run(command, capture_output=True, text=True, timeout=self.COMMAND_TIMEOUT)
        except subprocess.TimeoutExpired as e:
            output = self._decode_output(e.stdout) + self._decode_output(e.stderr)
            log_data = self._get_log_data(command, None, output)
            logger.error(log_data)
            raise PWarning(f"{error_message}: команда не завершилась за {self.COMMAND_TIMEOUT} секунд\n{output.strip()}")
        output = (process.stdout or "") + (process.stderr or "")

        log_data = self._get_log_data(command, process.returncode, output)

        if process.returncode:
            logger.error(log_data)
            raise PWarning(f"{error_message}\n{output.strip()}")

        logger.debug(log_data)
        return output

    @staticmethod
    def _decode_output(output: str | bytes | None) -> str:
        if output is None:
            return ""
        if isinstance(output, bytes):
            return output.decode("utf-8", errors="replace")
        return output

    def _get_log_data(self, command: list[str], returncode: int | None, output: str) -> dict:
        log_data = {
            "linux_command": {
                "command": subprocess.list2cmdline(command),
                "returncode": returncode,
                "output": output,
            },
        }
        if self.log_filter:
            log_data.update({"log_filter": self.log_filter})
        return log_data
