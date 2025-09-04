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
        usage = usage(
            model=model,  # noqa
            completion_tokens=usage_dict['output_tokens'],  # noqa
            prompt_tokens=usage_dict['input_tokens']  # noqa
        )

        answer = r_json['output'][-1]['content'][0]['text']
        response = response(
            text=answer,  # noqa
            usage=usage  # noqa
        )
        return response
