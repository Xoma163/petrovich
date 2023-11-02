from apps.bot.api.gigachat import GigaChat as GigaChatAPI
from apps.bot.classes.event.tg_event import TgEvent
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.commands.trusted.gpt.chatgpt import ChatGPT
from apps.bot.utils.utils import replace_markdown


class GigaChat(ChatGPT):
    name = "gigachat"
    names = ['гигачат', 'gigachad', 'гигачад']

    help_text = "чат GigaChat"

    help_texts = [
        "(фраза) - общение с ботом"
    ]

    def start(self) -> ResponseMessage:
        self.event: TgEvent

        if self.event.message.command in self.full_names:
            user_message = self.event.message.args_str_case
        else:
            user_message = self.event.message.raw

        messages = self.get_dialog(self.event, user_message)
        return self.text_chat(messages)

    def text_chat(self, messages, model=None) -> ResponseMessage:
        gc_api = GigaChatAPI()
        answer = gc_api.completions(messages, model)
        answer = answer.replace(">", "&gt;").replace("<", "&lt;").replace("&lt;pre&gt;", "<pre>").replace(
            "&lt;/pre&gt;", "</pre>")
        answer = replace_markdown(answer, self.bot)
        return ResponseMessage(ResponseMessageItem(text=answer, reply_to=self.event.message.id))
