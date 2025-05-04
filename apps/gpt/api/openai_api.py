import re

from requests.exceptions import SSLError, JSONDecodeError

from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PError, PWarning
from apps.bot.utils.proxy import get_proxies
from apps.bot.utils.utils import retry
from apps.gpt.api.responses import (
    GPTCompletionsResponse,
    GPTCompletionsVisionResponse,
    GPTVisionResponse
)
from apps.gpt.gpt_models.base import (
    GPTCompletionModel,
    GPTCompletionsVisionModel,
    GPTVisionModel
)
from apps.gpt.usage import (
    GPTCompletionsUsage,
    GPTCompletionsVisionUsage,
    GPTVisionUsage
)


class OpenAIAPI(API):
    ERRORS_MAP = {
        'content_policy_violation': "ChatGPT не может обработать запрос по политикам безопасности",
        503: "ChatGPT недоступен",
        'insufficient_quota': "Закончились деньги((",
        'invalid_api_key': "Некорректный API KEY. Проверьте свой ключ",
        'rate_limit_exceeded': "Слишком большой запрос",
        'model_not_found': "Модель не существует или у вас нет к ней доступа"
    }

    def do_completions_request(self, model: GPTCompletionModel, url, **kwargs) -> GPTCompletionsResponse:
        return self._do_request(GPTCompletionsUsage, GPTCompletionsResponse, model, url, **kwargs)  # noqa

    def do_vision_request(self, model: GPTVisionModel, url, **kwargs) -> GPTVisionResponse:
        return self._do_request(GPTVisionUsage, GPTVisionResponse, model, url, **kwargs)  # noqa

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
            completion_tokens=usage_dict['completion_tokens'],  # noqa
            prompt_tokens=usage_dict['prompt_tokens']  # noqa
        )

        answer = r_json['choices'][0]['message']['content']
        response = response(
            text=answer,  # noqa
            usage=usage  # noqa
        )
        return response

    @retry(3, SSLError, sleep_time=2)
    def do_request(self, url, **kwargs) -> dict:
        r = self.requests.post(url, proxies=get_proxies(), **kwargs)
        if r.status_code != 200:
            try:
                r_json = r.json()
            except JSONDecodeError as e:
                raise PWarning("Ошибка. Не получилось обработать запрос.") from e
        else:
            r_json = r.json()

        if error := r_json.get('error'):
            code = error.get('code')
            error_str = self.ERRORS_MAP.get(code, "Какая-то ошибка API ChatGPT")

            if code == "rate_limit_exceeded":
                message = error.get('message')
                _r = re.compile(r'Limit (\d*), Requested (\d+)Visit (.*) to').findall(message)
                if _r:
                    _r = _r[0]
                    error_str += f"\nЗапрошено токенов - {_r[1]}, доступно - {_r[0]}. Подробнее - {_r[2]}"

            raise PError(error_str)

        return r_json
