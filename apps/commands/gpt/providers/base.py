from abc import ABC, abstractmethod
from typing import Type

from apps.commands.gpt.api.base import GPTAPI
from apps.commands.gpt.enums import GPTProviderEnum
from apps.commands.gpt.messages.base import GPTMessages


class GPTProvider(ABC):
    @property
    @abstractmethod
    def type_enum(self) -> GPTProviderEnum:
        pass

    @property
    @abstractmethod
    def messages_class(self) -> Type[GPTMessages]:
        pass

    @property
    @abstractmethod
    def api_class(self) -> Type[GPTAPI]:
        pass
