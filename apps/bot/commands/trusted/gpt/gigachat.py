from apps.bot.api.gpt.gigachatgptapi import GigaChatGPTAPI
from apps.bot.api.gpt.response import GPTAPIResponse
from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.event.tg_event import TgEvent
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.commands.trusted.gpt.chatgpt import ChatGPT
from apps.bot.utils.utils import markdown_to_html
from apps.service.models import GPTPrePrompt


class GigaChat(ChatGPT):
    name = "gigachat"
    names = ['гигачат', 'gigachad', 'гигачад']

    help_text = HelpText(
        commands_text="чат GigaChat",
        help_texts=[
            HelpTextItem(Role.TRUSTED, [
                HelpTextItemCommand("(фраза)", "общение с ботом"),
                HelpTextItemCommand("(пересланное сообщение)", "общение с ботом"),
                HelpTextItemCommand("нарисуй (фраза/пересланное сообщение)", "генерация картинки"),
                HelpTextItemCommand("препромпт [конфа]", "посмотреть текущий препромпт"),
                HelpTextItemCommand("препромпт [конфа] (текст)", "добавить препромпт"),
                HelpTextItemCommand("препромпт [конфа] удалить", "удаляет препромпт"),
            ])
        ],
        extra_text=(
            "Если отвечать на сообщения бота через кнопку \"Ответить\" то будет продолжаться непрерывный диалог.\n"
            "В таком случае необязательно писать команду, можно просто текст\n\n"
            "Порядок использования препромптов в конфах:\n"
            "1) Персональный препромт конфы\n"
            "2) Персональный препромт\n"
            "3) Препромпт конфы"
        )
    )

    PREPROMPT_PROVIDER = GPTPrePrompt.GIGACHAT

    def start(self) -> ResponseMessage:
        self.event: TgEvent
        if self.event.message.args:
            arg0 = self.event.message.args[0]
            if arg0 in ["нарисуй", "draw"]:
                return self.draw_image()
            elif arg0 in ["препромпт", "препромт", "промпт", "промт", "preprompt", "prepromp", "prompt", "promt"]:
                return self.preprompt()

        user_message = self.get_user_msg(self.event)
        messages = self.get_dialog(user_message)
        return self.text_chat(messages)

    def text_chat(self, messages, model=None, **kwargs) -> ResponseMessage:
        if model is None:
            model = GigaChatGPTAPI.LATEST_MODEL
        gc_api = GigaChatGPTAPI(model, log_filter=self.event.log_filter)

        with ChatActivity(self.bot, ActivitiesEnum.TYPING, self.event.peer_id):
            response: GPTAPIResponse = gc_api.completions(messages)

        answer = markdown_to_html(response.text, self.bot)
        return ResponseMessage(ResponseMessageItem(text=answer, reply_to=self.event.message.id))

    def draw_image(self, model=None, **kwargs) -> ResponseMessage:
        if model is None:
            model = GigaChatGPTAPI.LATEST_MODEL

        if len(self.event.message.args) > 1:
            request_text = " ".join(self.event.message.args_case[1:])
        elif self.event.message.quote:
            request_text = self.event.message.quote
        elif self.event.fwd:
            request_text = self.event.fwd[0].message.raw
        else:
            raise PWarning("Должен быть текст или пересланное сообщение")

        chat_gpt_api = GigaChatGPTAPI(model, log_filter=self.event.log_filter)

        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_PHOTO, self.event.peer_id):
            response: GPTAPIResponse = chat_gpt_api.draw(self.event.message.args_str_case)

        if not response.images_bytes:
            raise PWarning("Не смог сгенерировать :(")

        attachments = [self.bot.get_photo_attachment(x) for x in response.images_bytes]

        answer = f'Результат генерации по запросу "{request_text}"'
        return ResponseMessage(
            ResponseMessageItem(text=answer, attachments=attachments, reply_to=self.event.message.id))
