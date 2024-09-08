from apps.bot.api.gpt.gpt import GPTAPI
from apps.bot.api.gpt.message import GPTMessages, GPTMessageRole
from apps.bot.api.gpt.response import GPTAPICompletionsResponse
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.utils.proxy import get_proxies
from petrovich.settings import env


class ClaudeGPTAPI(GPTAPI):
    API_KEY = env.str("CLAUDE_API_KEY")
    DEFAULT_COMPLETIONS_MODEL = "claude-3-5-sonnet-20240620"
    URL = "https://api.anthropic.com/v1/messages"

    def completions(self, messages: GPTMessages, use_image: bool = False) -> GPTAPICompletionsResponse:
        messages = messages.get_messages()
        preprompt = None
        if messages[0]['role'] == GPTMessageRole.SYSTEM.value:
            preprompt = messages[0]['content'][0]['text']
            messages = messages[1:]

        data = {
            "model": self.DEFAULT_COMPLETIONS_MODEL,
            "messages": messages,
            "max_tokens": 8192
        }
        if preprompt:
            data["system"] = preprompt

        r = self._do_request(data)
        if error := r.get("error", {}).get("message"):
            if "Your credit balance is too low" in error:
                raise PWarning("Закончились деньги((")

        answer = r['content'][0]['text']
        r = GPTAPICompletionsResponse(text=answer)
        return r

    def _do_request(self, data):
        return self.requests.post(self.URL, json=data, headers=self._headers(), proxies=get_proxies()).json()

    def _headers(self):
        return {
            "x-api-key": self.API_KEY,
            "anthropic-version": "2023-06-01"
        }
