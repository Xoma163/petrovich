import openai

from apps.bot.classes.Command import Command
from petrovich.settings import env


class GPT(Command):
    name = "gpt"
    names = ["гпт"]
    help_text = "чат GPT"
    help_texts = [
        "(фраза) - общение с ботом",
    ]

    def start(self):
        request_text = self.event.message.args_str_case

        openai.api_key = env.str("CHIMERA_SECRET_KEY")
        openai.api_base = "https://chimeragpt.adventblocks.cc/api/v1"

        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo-16k',
            messages=[
                {'role': 'user', 'content': request_text},
            ],
            stream=True,
            allow_fallback=True
        )

        result = []
        for chunk in response:
            result.append(chunk.choices[0].delta.get("content", ""))
        res = "".join(result)
        return {"text": res, "reply_to": self.event.message.id}
        # print(res)
