import dataclasses
from collections import deque


# https://github.com/MCCTeam/Minecraft-Console-Client/blob/master/MinecraftClient/Protocol/Handlers/Forge/ForgeInfo.cs
class DataTypes:
    """
    Перевод типов
    """

    @staticmethod
    def read_next_byte(cache: deque):
        return cache.popleft()

    def read_next_bool(self, cache: deque) -> bool:
        return self.read_next_byte(cache) != 0x00

    def read_next_string(self, cache: deque) -> str:
        length = self.read_next_varint(cache)
        if length > 0:
            return ''.join([chr(cache.popleft()) for _ in range(length)]).encode('utf-8').decode('utf-8')
        else:
            return ""

    @staticmethod
    def read_next_varint(cache: deque) -> int:
        i = 0
        j = 0
        while True:
            b = cache.popleft()
            i |= (b & 0x7F) << (j * 7)
            j += 1
            if j > 5:
                raise OverflowError("VarInt too big")
            if (b & 0x80) != 0x80:
                break
        return i


@dataclasses.dataclass
class ForgeModChannel:
    """
    Информация о каналах мода Forge
    """

    def __init__(self, channel_name, channel_version, required_on_client):
        self.channel_name = channel_name
        self.channel_version = channel_version
        self.required_on_client = required_on_client


@dataclasses.dataclass
class ForgeMod:
    """
    Информация о моде Forge
    """

    SERVER_ONLY = "IGNORED"

    def __init__(self, mod_id: str, mod_version: str, channels: list[ForgeModChannel]):
        self.mod_id: str = mod_id
        self.mod_version: str = mod_version
        self.channels: list[ForgeModChannel] = channels

    def __str__(self):
        if self.mod_version and self.mod_version != self.SERVER_ONLY:
            return f"{self.mod_id}={self.mod_version}"
        else:
            return self.mod_id

    def __repr__(self):
        return self.__str__()


class ForgeData:
    """
    Информация о Forge
    Парсинг Forge данных
    """

    VERSION_FLAG_IGNORE_SERVER_ONLY = 0b1

    def __init__(self, forge_data: dict):
        self.__data_package = forge_data['d']
        self.mods: list[ForgeMod] = []
        self.fml_version: str = forge_data['fmlNetworkVersion']

    def _decode_optimized(self) -> deque:
        size0 = ord(self.__data_package[0])
        size1 = ord(self.__data_package[1])
        size = size0 | (size1 << 15)
        package_data = []
        string_index = 2
        buffer = 0
        bits_in_buf = 0

        while string_index < len(self.__data_package):
            while bits_in_buf >= 8:
                package_data.append(buffer & 0xFF)
                buffer >>= 8
                bits_in_buf -= 8
            c = self.__data_package[string_index]
            buffer |= (ord(c) & 0x7FFF) << bits_in_buf
            bits_in_buf += 15
            string_index += 1

        while len(package_data) < size:
            package_data.append(buffer & 0xFF)
            buffer >>= 8
            bits_in_buf -= 8

        return deque(package_data)

    def decode_data(self):
        data_package_decoded = self._decode_optimized()
        data_types = DataTypes()

        # Не используется
        data_types.read_next_bool(data_package_decoded)  # truncated: boolean
        data_types.read_next_bool(data_package_decoded)  # truncated: boolean

        mods_size = data_types.read_next_byte(data_package_decoded)

        # Массив модов:
        for _ in range(mods_size):
            channel_size_and_version_flag = data_types.read_next_varint(data_package_decoded)
            channel_size = channel_size_and_version_flag >> 1

            is_ignore_server_only = (channel_size_and_version_flag & self.VERSION_FLAG_IGNORE_SERVER_ONLY) != 0

            mod_id = data_types.read_next_string(data_package_decoded)
            if is_ignore_server_only:
                mod_version = ForgeMod.SERVER_ONLY
            else:
                mod_version = data_types.read_next_string(data_package_decoded)

            channels = []
            for _ in range(channel_size):
                channel_name = data_types.read_next_string(data_package_decoded)
                channel_version = data_types.read_next_string(data_package_decoded)
                required_on_client = data_types.read_next_bool(data_package_decoded)

                channel = ForgeModChannel(channel_name, channel_version, required_on_client)
                channels.append(channel)
            self.mods.append(ForgeMod(mod_id, mod_version, channels))

    def sort_mods(self):
        self.mods = list(sorted(self.mods, key=lambda x: x.mod_id))
