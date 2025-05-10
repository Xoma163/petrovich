from enum import StrEnum


class GPTProviderEnum(StrEnum):
    CHATGPT = 'chatgpt'
    CLAUDE = 'claude'
    GROK = 'grok'


class GPTImageFormat(StrEnum):
    LANDSCAPE = "landscape"
    PORTAIR = "portair"
    SQUARE = "square"


class GPTImageQuality(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "medium"
    LOW = "low"
