from apps.bot.classes.const.exceptions import PWarning
from apps.bot.utils.proxy import get_proxies
from apps.gpt.api.base import (
    GPTAPI,
    CompletionsAPIMixin,
    VisionAPIMixin
)
from apps.gpt.api.responses import GPTVisionResponse, GPTCompletionsResponse
from apps.gpt.messages.base import GPTMessages
from apps.gpt.messages.consts import GPTMessageRole
from apps.gpt.models import (
    CompletionsModel,
    VisionModel
)
from apps.gpt.usage import GPTCompletionsUsage, GPTVisionUsage


class ClaudeAPI(
    GPTAPI,
    CompletionsAPIMixin,
    VisionAPIMixin,
):
    @property
    def headers(self):
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

    def check_key(self) -> bool:
        from apps.gpt.messages.providers.claude import ClaudeMessages

        messages = ClaudeMessages()
        messages.add_message(GPTMessageRole.USER, "привет")
        url = f"{self.base_url}/messages"

        json_data = {
            "model": "claude-3-haiku-20240307",
            "messages": messages.get_messages(),
            "max_tokens": 50
        }

        try:
            response_json = self.do_request(url, json=json_data)
            return 'usage' in response_json
        except Exception:
            return False

    # ---------- base ---------- #

    base_url = "https://api.anthropic.com/v1"

    def do_request(self, url, **kwargs) -> dict:
        r_json = self.requests.post(url, headers=self.headers, proxies=get_proxies(), **kwargs).json()

        if error := r_json.get("error", {}).get("message"):
            if "Your credit balance is too low" in error:
                raise PWarning("Закончились деньги((")
        return r_json

    # ---------- completions ---------- #

    completions_url = f"{base_url}/messages"

    def completions(self, messages: GPTMessages, model: CompletionsModel) -> GPTCompletionsResponse:
        preprompt = None
        messages = messages.get_messages()
        if messages[0]['role'] == GPTMessageRole.SYSTEM:
            preprompt = messages[0]['content'][0]['text']
            messages = messages[1:]

        data = {
            "model": model.name,
            "messages": messages,
            "max_tokens": 8192
        }
        if preprompt:
            data["system"] = preprompt

        r_json = self.do_request(self.completions_url, json=data)

        usage = GPTCompletionsUsage(
            model=model,  # noqa
            completion_tokens=r_json['usage']['output_tokens'],
            prompt_tokens=r_json['usage']['input_tokens'],
        )

        answer = r_json['content'][0]['text']
        response = GPTCompletionsResponse(
            text=answer,
            usage=usage
        )
        return response

    # ---------- vision ---------- #

    vision_url = f"{base_url}/chat/completions"

    def vision(self, messages: GPTMessages, model: VisionModel) -> GPTVisionResponse:
        preprompt = None
        messages = messages.get_messages()
        if messages[0]['role'] == GPTMessageRole.SYSTEM:
            preprompt = messages[0]['content'][0]['text']
            messages = messages[1:]

        data = {
            "model": model.name,
            "messages": messages,
            "max_tokens": 8192
        }
        if preprompt:
            data["system"] = preprompt

        r_json = self.do_request(self.completions_url, json=data)

        usage = GPTVisionUsage(
            model=model,  # noqa
            completion_tokens=r_json['usage']['output_tokens'],
            prompt_tokens=r_json['usage']['input_tokens'],
        )

        answer = r_json['content'][0]['text']
        response = GPTVisionResponse(
            text=answer,
            usage=usage
        )
        return response
