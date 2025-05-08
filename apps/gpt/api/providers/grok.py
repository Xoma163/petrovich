from apps.gpt.api.base import CompletionsAPIMixin, VisionAPIMixin, ImageDrawAPIMixin
from apps.gpt.api.openai_api import OpenAIAPI
from apps.gpt.api.responses import GPTVisionResponse, GPTImageDrawResponse, GPTCompletionsResponse
from apps.gpt.enums import GPTImageFormat, GPTImageQuality
from apps.gpt.gpt_models.base import GPTModels, GPTVisionModel, GPTImageDrawModel, GPTCompletionModel
from apps.gpt.gpt_models.providers.grok import GrokModels, GrokCompletionModels, GrokVisionModels, GrokImageDrawModels
from apps.gpt.messages.base import GPTMessages


class GrokAPI(
    OpenAIAPI,
    CompletionsAPIMixin,
    VisionAPIMixin,
    ImageDrawAPIMixin,
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

    completions_url = f"{base_url}/chat/completions"
    default_completions_model: GPTCompletionModel = GrokCompletionModels.grok_3

    def completions(self, messages: GPTMessages) -> GPTCompletionsResponse:
        model = self.get_completions_model()
        payload = {
            "model": model.name,
            "messages": messages.get_messages()
        }

        return self.do_completions_request(model, self.completions_url, json=payload, headers=self.headers)

    # ---------- vision ---------- #

    vision_url = f"{base_url}/chat/completions"
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

    image_draw_url = f"{base_url}/images/generations"
    default_image_draw_model: GPTImageDrawModel = GrokImageDrawModels.grok_2_image

    def get_image_draw_model(self, gpt_image_format: GPTImageFormat, quality: GPTImageQuality) -> GPTImageDrawModel:
        return self.default_image_draw_model

    def draw_image(
            self,
            prompt: str,
            image_format: GPTImageFormat,
            quality: GPTImageQuality,
            count: int = 1,  # quality are not supported by xAI API at the moment.
    ) -> GPTImageDrawResponse:
        model = self.get_image_draw_model(image_format, quality)
        payload = {
            'model': model.name,
            'prompt': prompt,
            'n': count,
            # 'size': model.size # size are not supported by xAI API at the moment.
            'response_format': 'b64_json',
        }
        return self.do_image_request(
            model=model,
            url=self.image_draw_url,
            json=payload,
            count=count,
            headers=self.headers,
            log=False
        )
