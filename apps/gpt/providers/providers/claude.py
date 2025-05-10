from apps.gpt.api.base import GPTAPI
from apps.gpt.api.providers.claude import ClaudeAPI
from apps.gpt.enums import GPTProviderEnum
from apps.gpt.messages.base import GPTMessages
from apps.gpt.messages.providers.claude import ClaudeMessages
from apps.gpt.providers.base import GPTProvider


class ClaudeProvider(GPTProvider):
    name: GPTProviderEnum = GPTProviderEnum.CLAUDE
    messages_class: type[GPTMessages] = ClaudeMessages
    api_class: type[GPTAPI] = ClaudeAPI
