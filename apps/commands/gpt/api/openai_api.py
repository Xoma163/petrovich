import concurrent
import logging
import re
from abc import ABC
from concurrent.futures import ThreadPoolExecutor

from requests.exceptions import SSLError, JSONDecodeError

from apps.bot.core.messages.attachments.photo import PhotoAttachment
from apps.commands.gpt.api.base import GPTAPI
from apps.commands.gpt.api.responses import (
    GPTCompletionsResponse,
    GPTCompletionsVisionResponse,
    GPTVisionResponse,
    GPTImageDrawResponse
)
from apps.commands.gpt.models import (
    CompletionsModel,
    VisionModel,
    ImageDrawModel,
    GPTCompletionsVisionModel
)
from apps.commands.gpt.usage import (
    GPTCompletionsUsage,
    GPTCompletionsVisionUsage,
    GPTVisionUsage,
    GPTImageDrawUsage
)
from apps.shared.decorators import retry
from apps.shared.exceptions import PError, PWarning

logger = logging.getLogger('openai')


class OpenAIAPI(GPTAPI, ABC):
    ERRORS_MAP = {
        'content_policy_violation': "ChatGPT не может обработать запрос по политикам безопасности",
        503: "ChatGPT недоступен",
        'insufficient_quota': "Закончились деньги((",
        'invalid_api_key': "Некорректный API KEY. Проверьте свой ключ",
        'rate_limit_exceeded': "Слишком большой запрос",
        'model_not_found': "Модель не существует или у вас нет к ней доступа"
    }

    def do_completions_request(self, model: CompletionsModel, url, **kwargs) -> GPTCompletionsResponse:
        return self._do_request(GPTCompletionsUsage, GPTCompletionsResponse, model, url, **kwargs)  # noqa

    def do_vision_request(self, model: VisionModel, url, **kwargs) -> GPTVisionResponse:
        return self._do_request(GPTVisionUsage, GPTVisionResponse, model, url, **kwargs)  # noqa

    def do_image_request(self, model: ImageDrawModel, count: int, url: str, **kwargs) -> GPTImageDrawResponse:
        if count > 1:
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(self.fetch_image_request, url, **kwargs) for _ in range(count)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
            images_bytes = [image_bytes for image_bytes, _ in results]
            images_prompt = results[0][1]
        else:
            image_bytes, prompt = self.fetch_image_request(url, **kwargs)
            images_bytes = [image_bytes]
            images_prompt = prompt

        usage = GPTImageDrawUsage(
            model=model,  # noqa
            images_count=count,
        )
        return GPTImageDrawResponse(
            images_bytes=images_bytes,
            images_prompt=images_prompt,
            usage=usage,
        )

    def fetch_image_request(self, url, **kwargs) -> tuple[bytes, str | None]:
        r_json = self.do_request(url, **kwargs)
        image_data = r_json['data'][0]
        base64_image = PhotoAttachment.decode_base64(image_data['b64_json'])
        return base64_image, image_data.get('revised_prompt')

    def _do_request(
            self,
            usage: type[GPTCompletionsVisionUsage],
            response: type[GPTCompletionsVisionResponse],
            model: GPTCompletionsVisionModel,
            url,
            **kwargs
    ) -> GPTCompletionsVisionResponse:
        r_json = self.do_request(url, **kwargs)
        usage_dict = r_json.get('usage')
        usage = usage(
            model=model,  # noqa
            input_tokens=usage_dict['prompt_tokens'],  # noqa
            output_tokens=usage_dict['completion_tokens'],  # noqa
        )

        answer = r_json['choices'][0]['message']['content']
        response = response(
            text=answer,  # noqa
            usage=usage  # noqa
        )
        return response

    @retry(3, SSLError, sleep_time=2)
    def do_request(self, url, **kwargs) -> dict:
        # kwargs['headers']['Content-Type'] = "application/json"
        r = self.requests.post(url, **kwargs)
        if r.status_code != 200:
            try:
                r_json = r.json()
            except JSONDecodeError as e:
                raise PWarning("Ошибка. Не получилось обработать запрос.") from e
        else:
            r_json = r.json()

        if error := r_json.get('error'):
            logger.error(str(r_json))

            # grok
            if isinstance(error, str):
                code = None
                if 'used all available credits' in error:
                    code = 'insufficient_quota'
            # chatgpt
            else:
                code = error.get('code')
            error_str = self.ERRORS_MAP.get(code, "Какая-то ошибка OpenAI API")

            if code == "rate_limit_exceeded":
                message = error.get('message')
                _r = re.compile(r'Limit (\d*), Requested (\d+)Visit (.*) to').findall(message)
                if _r:
                    _r = _r[0]
                    error_str += f"\nЗапрошено токенов - {_r[1]}, доступно - {_r[0]}. Подробнее - {_r[2]}"

            raise PError(error_str)

        return r_json

    def _check_key(self, model, headers) -> bool:
        from apps.commands.gpt.messages.providers.chatgpt import ChatGPTMessages
        from apps.commands.gpt.messages.consts import GPTMessageRole

        messages = ChatGPTMessages()
        messages.add_message(GPTMessageRole.USER, "привет")
        url = f"{self.base_url}/responses"
        json_data = {
            "model": model,
            "input": messages.get_messages(),
            "max_output_tokens": 50
        }
        try:
            response_json = self.do_request(
                url,
                json=json_data,
                headers=headers,
            )
            return 'usage' in response_json
        except Exception:
            return False
