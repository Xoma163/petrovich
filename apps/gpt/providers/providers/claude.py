from apps.gpt.api.base import GPTAPI
from apps.gpt.api.providers.claude import ClaudeAPI
from apps.gpt.enums import GPTProviderEnum
from apps.gpt.messages.base import GPTMessages
from apps.gpt.messages.providers.claude import ClaudeMessages
from apps.gpt.providers.base import GPTProvider
from petrovich.settings import env


class ClaudeProvider(GPTProvider):
    type_enum: GPTProviderEnum = GPTProviderEnum.CLAUDE
    messages_class: type[GPTMessages] = ClaudeMessages
    api_class: type[GPTAPI] = ClaudeAPI
    api_key: str = env.str("CLAUDE_API_KEY")
