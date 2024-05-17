import dataclasses
import json
import socket
import struct
import time

from apps.bot.commands.minecraft.forge import ForgeMod, ForgeData


@dataclasses.dataclass
class MinecraftPlayerData:
    """
    Информация о игроке майнкрафта
    """

    def __init__(self, _id, name):
        self.id = _id
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()


@dataclasses.dataclass
class MinecraftServerData:
    """
    Информация о сервере майнкрафта
    """

    def __init__(
            self,
            favicon: str | None = None,
            enforces_secure_chat: bool | None = None,
            description: str | None = None,
            players_online: int | None = None,
            players_max: int | None = None,
            version: str | None = None,
            version_protocol: str | None = None,
            latency: float | None = None,
            players: list[MinecraftPlayerData] = None,
            forge_data: list[ForgeMod] = None,
    ):
        self.online = True
        self.favicon: str = favicon  # base64
        self.enforces_secure_chat: bool = enforces_secure_chat
        self.description: str = description
        self.players_online: int = players_online
        self.players_max: int = players_max
        self.version: str = version
        self.version_protocol: str = version_protocol
        self.latency: float = latency
        self.forge_data: ForgeData | None = forge_data if forge_data else None
        self.players: list[MinecraftPlayerData] = players if players else []

    def __str__(self):
        return self.description


class MinecraftServerStatus:
    """
    Получение данных о сервере майнкрафта с парсингом forge
    """

    def __init__(self, host, port):
        self.host = host
        self.port = port

    @staticmethod
    def pack_varint(data):
        """ Pack an integer as a varint """
        result = b""
        while True:
            byte = data & 0x7F
            data >>= 7
            if data:
                result += struct.pack(">B", byte | 0x80)
            else:
                result += struct.pack(">B", byte)
                break
        return result

    def _get_status(self) -> dict:
        """
        Получение статуса сервера с помощью подключения по сокету
        """
        start_time = time.time()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)
            sock.connect((self.host, self.port))

            # Handshake packet
            handshake_packet = b""
            handshake_packet += self.pack_varint(1)  # Protocol version (47 for 1.8.9) Не влияет
            handshake_packet += self.pack_varint(len(self.host)) + self.host.encode('utf-8')  # Host
            handshake_packet += struct.pack('>H', self.port)  # Port
            handshake_packet += self.pack_varint(1)  # Next state (1 for status)

            # Packet length + packet ID for handshake
            packet = self.pack_varint(len(handshake_packet) + 1) + b"\x00" + handshake_packet
            sock.sendall(packet)

            # Request packet
            request_packet = self.pack_varint(1) + b"\x00"
            sock.sendall(request_packet)

            # Read response length
            length = 0
            shift = 0
            while True:
                byte = sock.recv(1)
                if byte:
                    b = ord(byte)
                    length |= (b & 0x7F) << shift
                    if not (b & 0x80):
                        break
                    shift += 7
                else:
                    raise ValueError("Unexpected EOF while reading varint")

            # Read response
            response = b""
            while len(response) < length:
                response += sock.recv(length - len(response))
            response_data = response.decode('utf-8', errors='ignore')
        elapsed_time = time.time() - start_time
        # Extract JSON from the response
        try:
            json_start = response_data.index("{")
            json_end = response_data.rindex("}") + 1
            response_json = json.loads(response_data[json_start:json_end])
        except ValueError:
            response_json = {}

        response_json["latency"] = elapsed_time

        return response_json

    def get_server_data(self, parse_forge_data: bool = False) -> MinecraftServerData:
        """
        Маппинг данных
        """
        server_status = self._get_status()
        forge_data = None
        if parse_forge_data:
            if _forge_data := server_status.get('forgeData'):
                forge_data = ForgeData(_forge_data)
                forge_data.decode_data()
                forge_data.sort_mods()

        players = []
        if _players := server_status['players'].get('sample'):
            players = [MinecraftPlayerData(_id=player_raw['id'], name=player_raw['name']) for player_raw in _players]

        return MinecraftServerData(
            favicon=server_status['favicon'],
            enforces_secure_chat=server_status['enforcesSecureChat'],
            description=server_status['description']['text'],
            players_online=server_status['players']['online'],
            players_max=server_status['players']['max'],
            version=server_status['version']['name'],
            version_protocol=server_status['version']['protocol'],
            latency=server_status['latency'],
            players=players,
            forge_data=forge_data,
        )
