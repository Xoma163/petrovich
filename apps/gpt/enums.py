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
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GPTReasoningEffortLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class GPTVerbosityLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

