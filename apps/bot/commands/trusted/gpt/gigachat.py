from apps.bot.api.gpt.gigachatgptapi import GigaChatGPTAPI
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
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
            "В таком случае необязательно писать команду, можно просто текст"
        ),
        help_texts=[
            HelpTextItem(Role.TRUSTED, [
                "(фраза/пересланное сообщение) - общение с ботом",
                "нарисуй (фраза/пересланное сообщение) - генерация картинки"
            ])
        ]
    )

    def start(self) -> ResponseMessage:
        self.event: TgEvent
        if self.event.message.args and self.event.message.args[0] == "нарисуй":
            return self.draw_image()

        user_message = self.get_user_msg(self.event)
        messages = self.get_dialog(user_message)
        return self.text_chat(messages)

    def text_chat(self, messages, model=None) -> ResponseMessage:
        if model is None:
            model = GigaChatGPTAPI.PRO_MODEL
        gc_api = GigaChatGPTAPI(model)

        try:
            self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.TYPING)
            answer = gc_api.completions(messages)
        finally:
            self.bot.stop_activity_thread()

        answer = markdown_to_html(answer, self.bot)
        return ResponseMessage(ResponseMessageItem(text=answer, reply_to=self.event.message.id))

    def draw_image(self, model=None) -> ResponseMessage:
        if model is None:
            model = GigaChatGPTAPI.PRO_MODEL
        if len(self.event.message.args) > 1:
            request_text = " ".join(self.event.message.args_case[1:])
        elif self.event.fwd:
            request_text = self.event.fwd[0].message.raw
        else:
            raise PWarning("Должен быть текст или пересланное сообщение")

        chat_gpt_api = GigaChatGPTAPI(model)

        try:
            self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.UPLOAD_PHOTO)
            image = chat_gpt_api.draw(self.event.message.args_str_case)
        finally:
            self.bot.stop_activity_thread()

        if not image:
            raise PWarning("Не смог сгенерировать :(")

        attachments = [self.bot.get_photo_attachment(image)]

        answer = f'Результат генерации по запросу "{request_text}"'
        return ResponseMessage(
            ResponseMessageItem(text=answer, attachments=attachments, reply_to=self.event.message.id))
