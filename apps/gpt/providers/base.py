from abc import ABC, abstractmethod
from typing import Type

from apps.gpt.api.base import GPTAPI
from apps.gpt.enums import GPTProviderEnum
from apps.gpt.messages.base import GPTMessages


class GPTProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> GPTProviderEnum:
        pass

    @property
    @abstractmethod
    def messages_class(self) -> Type[GPTMessages]:
        pass

    @property
    @abstractmethod
    def api_class(self) -> Type[GPTAPI]:
        pass

