from enum import StrEnum


class GPTProviderEnum(StrEnum):
    CHATGPT = 'chatgpt'
    CLAUDE = 'claude'
    GROK = 'grok'


class GPTImageFormat(StrEnum):
    ALBUM = "album"
    PORTAIR = "portair"
    SQUARE = "square"


class GPTImageQuality(StrEnum):
    STANDARD = "standard"
    HIGH = "hd"
