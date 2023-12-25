from apps.bot.api.gpt.gigachat import GigaChat as GigaChatAPI
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Role
from apps.bot.classes.event.tg_event import TgEvent
from apps.bot.classes.help_text import HelpText, HelpTextItem
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.commands.trusted.gpt.chatgpt import ChatGPT
from apps.bot.utils.utils import markdown_to_html


class GigaChat(ChatGPT):
    name = "gigachat"
    names = ['гигачат', 'gigachad', 'гигачад']

    help_text = HelpText(
        commands_text="чат GigaChat",
        extra_text=(
            "Если отвечать на сообщения бота через кнопку \"Ответить\" то будет продолжаться непрерывный диалог.\n"
            "В таком случае необязательно писать команду, можно просто текст\n\n"
        ),
        help_texts=[
            HelpTextItem(Role.TRUSTED, [
                "(фраза) - общение с ботом",
            ])
        ]
    )

    def start(self) -> ResponseMessage:
        self.event: TgEvent

        user_message = self.get_user_msg(self.event)
        messages = self.get_dialog(user_message)
        return self.text_chat(messages)

    def text_chat(self, messages, model=None) -> ResponseMessage:
        if model is None:
            model = GigaChatAPI.PRO_MODEL
        gc_api = GigaChatAPI(model)

        try:
            self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.TYPING)
            answer = gc_api.completions(messages)
        finally:
            self.bot.stop_activity_thread()

        answer = markdown_to_html(answer, self.bot)
        return ResponseMessage(ResponseMessageItem(text=answer, reply_to=self.event.message.id))
