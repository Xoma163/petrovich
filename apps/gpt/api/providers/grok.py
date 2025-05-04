import base64

from apps.gpt.api.base import GPTAPI, CompletionsMixin, VisionMixin, ImageDrawMixin
from apps.gpt.api.openai_api import OpenAIAPI
from apps.gpt.api.responses import GPTVisionResponse, GPTImageDrawResponse, GPTCompletionsResponse
from apps.gpt.enums import GPTImageFormat, GPTImageQuality
from apps.gpt.gpt_models.base import GPTModels, GPTVisionModel, GPTImageDrawModel, GPTCompletionModel
from apps.gpt.gpt_models.providers.grok import GrokModels, GrokCompletionModels, GrokVisionModels, GrokImageDrawModels
from apps.gpt.messages.base import GPTMessages
from apps.gpt.usage import GPTImageDrawUsage


class GrokAPI(
    GPTAPI,
    OpenAIAPI,
    CompletionsMixin,
    VisionMixin,
    ImageDrawMixin,
):
    @property
    def headers(self) -> dict:
        return {
            'Authorization': f"Bearer {self.api_key}"
        }

    # ---------- base ---------- #

    base_url = "https://api.x.ai/v1"
    api_key_env_name = "GROK_API_KEY"
    gpt_settings_key_field = "grok_key"
    gpt_settings_model_field = "grok_model"
    models: type[GPTModels] = GrokModels

    # ---------- completions ---------- #

    @property
    def completions_url(self) -> str:
        return f"{self.base_url}/chat/completions"

    default_completions_model: GPTCompletionModel = GrokCompletionModels.grok_3

    def completions(self, messages: GPTMessages) -> GPTCompletionsResponse:
        model = self.get_completions_model()
        payload = {
            "model": model.name,
            "messages": messages.get_messages()
        }

        return self.do_completions_request(model, self.completions_url, json=payload, headers=self.headers)

    # ---------- vision ---------- #

    @property
    def vision_url(self) -> str:
        return f"{self.base_url}/chat/completions"

    default_vision_model: GPTVisionModel = GrokVisionModels.grok_2_vision

    def get_vision_model(self) -> GPTVisionModel:
        return self.default_vision_model

    def vision(self, messages: GPTMessages) -> GPTVisionResponse:
        model = self.get_vision_model()
        payload = {
            "model": model.name,
            "messages": messages.get_messages()
        }
        return self.do_vision_request(model, self.vision_url, json=payload, headers=self.headers)

    # ---------- image draw ---------- #

    @property
    def draw_url(self) -> str:
        return f"{self.base_url}/images/generations"

    default_draw_model: GPTImageDrawModel = GrokImageDrawModels.grok_2_image

    def get_draw_model(self, gpt_image_format: GPTImageFormat, quality: GPTImageQuality) -> GPTImageDrawModel:
        return self.default_draw_model

    def image_draw(
            self,
            prompt: str,
            image_format: GPTImageFormat,
            quality: GPTImageQuality,
            count: int = 1,  # quality are not supported by xAI API at the moment.
    ) -> GPTImageDrawResponse:
        """
        Метод для рисования GPTAPI, переопределяется не у всех наследников
        """
        model = self.get_draw_model(image_format, quality)

        payload = {
            'prompt': prompt,
            'n': count,
            'response_format': 'b64_json',
            'model': model.name
        }
        result = self.do_request(self.draw_url, json=payload)

        image_prompt = result['data'][0]['revised_prompt']
        usage = GPTImageDrawUsage(
            model=model,
            images_count=count,
        )
        r = GPTImageDrawResponse(
            images_bytes=[base64.b64decode(x['b64_json']) for x in result['data']],
            images_prompt=image_prompt,
            usage=usage
        )
        return r
