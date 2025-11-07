from abc import ABC

from apps.gpt.api.openai_api import OpenAIAPI
from apps.gpt.api.responses import (
    GPTCompletionsVisionResponse
)
from apps.gpt.models import (
    GPTCompletionsVisionModel
)
from apps.gpt.usage import (
    GPTCompletionsVisionUsage
)


class OpenAIResponsesAPI(OpenAIAPI, ABC):
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
        output = r_json.get("output", [])
        usage = usage(
            model=model,  # noqa
            input_tokens=usage_dict['input_tokens'] - usage_dict['input_tokens_details']['cached_tokens'],  # noqa
            input_cached_tokens=usage_dict['input_tokens_details']['cached_tokens'],  # noqa
            output_tokens=usage_dict['output_tokens'],  # noqa
            web_search_tokens=sum(x.get("type") == "web_search_call" for x in output),  # noqa
        )

        answer = output[-1]['content'][0]['text']
        response = response(
            text=answer,  # noqa
            usage=usage  # noqa
        )
        return response
