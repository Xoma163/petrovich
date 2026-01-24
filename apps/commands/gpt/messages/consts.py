from enum import StrEnum


class GPTMessageRole(StrEnum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'
