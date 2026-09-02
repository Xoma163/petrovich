import dataclasses
import logging
import re
import socket
import struct
import subprocess
import time

from apps.shared.exceptions import PWarning


logger = logging.getLogger("bot")


class ZomboidRconClient:
    SERVERDATA_RESPONSE_VALUE = 0
    SERVERDATA_EXECCOMMAND = 2
    SERVERDATA_AUTH = 3
    AUTH_PACKETS_COUNT = 2
    COMMAND_READ_DELAY = 0.5

    def __init__(self, host: str, port: int, password: str, timeout: int = 10):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self.request_id = 1
        self.socket: socket.socket | None = None

    def __enter__(self):
        self.socket = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.socket.settimeout(3)
        self._authenticate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.socket:
            self.socket.close()

    def command(self, command: str) -> str:
        request_id = self._send_packet(self.SERVERDATA_EXECCOMMAND, command)
        time.sleep(self.COMMAND_READ_DELAY)

        chunks = []
        try:
            while True:
                response_id, _, body = self._read_packet()
                if response_id == request_id and body:
                    chunks.append(body)
        except socket.timeout:
            pass

        return "".join(chunks)

    def _authenticate(self):
        request_id = self._send_packet(self.SERVERDATA_AUTH, self.password)
        responses = []
        for _ in range(self.AUTH_PACKETS_COUNT):
            try:
                responses.append(self._read_packet())
            except socket.timeout:
                break

        response_ids = [response_id for response_id, _, _ in responses]
        if -1 in response_ids:
            raise PWarning("Не смог авторизоваться в Zomboid RCON")
        if request_id not in response_ids:
            raise PWarning("Zomboid RCON вернул неожиданный ответ при авторизации")

    def _send_packet(self, packet_type: int, body: str) -> int:
        if not self.socket:
            raise PWarning("Zomboid RCON не подключён")

        request_id = self.request_id
        self.request_id += 1

        body_bytes = body.encode("utf-8")
        packet = struct.pack("<ii", request_id, packet_type) + body_bytes + b"\x00\x00"
        self.socket.sendall(struct.pack("<i", len(packet)) + packet)
        return request_id

    def _read_packet(self) -> tuple[int, int, str]:
        if not self.socket:
            raise PWarning("Zomboid RCON не подключён")

        length_bytes = self._recv_exact(4)
        length = struct.unpack("<i", length_bytes)[0]
        response = self._recv_exact(length)
        request_id, packet_type = struct.unpack("<ii", response[:8])
        body = response[8:-2].decode("utf-8", errors="replace")
        return request_id, packet_type, body

    def _recv_exact(self, length: int) -> bytes:
        if not self.socket:
            raise PWarning("Zomboid RCON не подключён")

        chunks = []
        received = 0
        while received < length:
            chunk = self.socket.recv(length - received)
            if not chunk:
                raise PWarning("Zomboid RCON закрыл соединение")
            chunks.append(chunk)
            received += len(chunk)
        return b"".join(chunks)


@dataclasses.dataclass
class ZomboidServerData:
    players_online: int | None = None
    players: list[str] = dataclasses.field(default_factory=list)
    raw_status: str = ""


class ZomboidServer:
    COMMAND_TIMEOUT = 300
    ANSI_ESCAPE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    RESTART_COMMAND = ["sudo", "/usr/local/sbin/zomboid-restart-if-empty-updates", "--force"]
    FORCE_RESTART_COMMAND = ["sudo", "systemctl", "restart", "zomboid"]
    STATUS_COMMAND = ["sudo", "-u", "zomboid", "-H", "bash", "-lc", "cd /opt/zomboid && ./pzserver send players"]

    def __init__(
        self,
        rcon_host: str,
        rcon_port: int,
        rcon_password: str,
        log_filter: dict | None = None,
    ):
        self.rcon_host = rcon_host
        self.rcon_port = rcon_port
        self.rcon_password = rcon_password
        self.log_filter = log_filter

    def restart(self) -> str:
        return self._run_command(self.RESTART_COMMAND, "Не смог перезапустить Zomboid")

    def force_restart(self) -> str:
        return self._run_command(self.FORCE_RESTART_COMMAND, "Не смог форсированно перезапустить Zomboid")

    def get_server_info(self) -> ZomboidServerData:
        output = self._run_rcon_command("players")
        return self.parse_players(output)

    def _run_rcon_command(self, command: str) -> str:
        if not self.rcon_password:
            raise PWarning("Не настроен пароль Zomboid RCON")

        try:
            with ZomboidRconClient(self.rcon_host, self.rcon_port, self.rcon_password) as client:
                output = client.command(command)
        except PWarning:
            raise
        except (OSError, socket.timeout) as e:
            logger.error(self._get_rcon_log_data(command, str(e)))
            raise PWarning(f"Не смог получить статус Zomboid через RCON\n{e}")

        logger.debug(self._get_rcon_log_data(command, output))
        return output

    @classmethod
    def parse_players(cls, output: str) -> ZomboidServerData:
        output = cls.strip_ansi(output)
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

    @classmethod
    def strip_ansi(cls, output: str) -> str:
        return cls.ANSI_ESCAPE_RE.sub("", output)

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

    def _get_rcon_log_data(self, command: str, output: str) -> dict:
        log_data = {
            "zomboid_rcon": {
                "host": self.rcon_host,
                "port": self.rcon_port,
                "command": command,
                "output": output,
            },
        }
        if self.log_filter:
            log_data.update({"log_filter": self.log_filter})
        return log_data
