from apps.bot.classes.const.exceptions import PWarning
from apps.bot.utils.proxy import get_proxies
from apps.gpt.api.base import GPTAPI, CompletionsMixin, VisionMixin
from apps.gpt.api.responses import GPTVisionResponse, GPTCompletionsResponse
from apps.gpt.gpt_models.base import GPTModels, GPTVisionModel, GPTCompletionModel
from apps.gpt.gpt_models.providers.claude import ClaudeModels, ClaudeVisionModels, ClaudeCompletionModels
from apps.gpt.messages.base import GPTMessages
from apps.gpt.messages.consts import GPTMessageRole
from apps.gpt.usage import GPTCompletionsUsage, GPTVisionUsage


class ClaudeAPI(
    GPTAPI,
    CompletionsMixin,
    VisionMixin,
):
    @property
    def headers(self):
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

    # ---------- base ---------- #

    base_url = "https://api.anthropic.com/v1"
    api_key_env_name = "CLAUDE_API_KEY"
    gpt_settings_key_field = "claude_key"
    gpt_settings_model_field = "claude_model"
    models: type[GPTModels] = ClaudeModels

    def do_request(self, url, **kwargs) -> dict:
        r_json = self.requests.post(url, headers=self.headers, proxies=get_proxies(), **kwargs).json()

        if error := r_json.get("error", {}).get("message"):
            if "Your credit balance is too low" in error:
                raise PWarning("Закончились деньги((")
        return r_json

    # ---------- completions ---------- #

    @property
    def completions_url(self) -> str:
        return f"{self.base_url}/messages"

    default_completions_model: GPTCompletionModel = ClaudeCompletionModels.claude_3_5_haiku

    def completions(self, messages: GPTMessages) -> GPTCompletionsResponse:
        model = self.get_completions_model()

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
            model=model,
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

    @property
    def vision_url(self) -> str:
        return f"{self.base_url}/chat/completions"

    default_vision_model: GPTVisionModel = ClaudeVisionModels.claude_3_5_haiku_vision

    def get_vision_model(self) -> GPTVisionModel:
        return self.default_vision_model

    def vision(self, messages: GPTMessages) -> GPTVisionResponse:
        model = self.get_vision_model()

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
            model=model,
            completion_tokens=r_json['usage']['output_tokens'],
            prompt_tokens=r_json['usage']['input_tokens'],
        )

        answer = r_json['content'][0]['text']
        response = GPTVisionResponse(
            text=answer,
            usage=usage
        )
        return response
