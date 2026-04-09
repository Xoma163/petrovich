from typing import Callable

from apps.commands.gpt.api.base import CompletionsAPIMixin
from apps.commands.gpt.api.openai_responses_api import OpenAIResponsesAPI
from apps.commands.gpt.api.providers.chatgpt import ChatGPTAPI
from apps.commands.gpt.api.responses import GPTCompletionsResponse
from apps.commands.gpt.messages.base import GPTMessages
from apps.commands.gpt.models import CompletionsModel


class ChatGPTOAuthAPI(OpenAIResponsesAPI, CompletionsAPIMixin):
    base_url = "https://chatgpt.com/backend-api/codex"
    completions_url = f"{base_url}/responses"

    def __init__(self, api_key: str, account_id: str | None = None, *args, **kwargs):
        super().__init__(api_key=api_key, *args, **kwargs)
        self.account_id = account_id

    @property
    def headers(self):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "responses=experimental",
        }
        if self.account_id:
            headers["ChatGPT-Account-Id"] = self.account_id
        return headers

    def check_key(self) -> bool:
        return bool(self.api_key)

    def completions(
        self,
        messages: GPTMessages,
        model: CompletionsModel,
        extra_data: dict,
        callback_func: Callable | None = None,
    ) -> GPTCompletionsResponse:
        payload: dict = {
            "model": model.name,
            "instructions": "",
            "store": False,
        }
        if callback_func:
            payload["stream"] = True

        preprompt, messages_dict = messages.get_preprompt_and_messages()
        if preprompt:
            payload["instructions"] = preprompt
        payload["input"] = messages_dict
        payload["include"] = [
            "reasoning.encrypted_content",
            "web_search_call.action.sources",
        ]

        ChatGPTAPI._set_gpt_5_payload(payload, model, extra_data)

        return self.do_completions_request(
            model,
            self.completions_url,
            json=payload,
            headers=self.headers,
            stream=True if callback_func else False,
            callback_func=callback_func,
        )
