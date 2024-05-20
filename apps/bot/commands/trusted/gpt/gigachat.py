from apps.bot.api.gpt.gigachatgptapi import GigaChatGPTAPI
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.commands.chatgpt import ChatGPT
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
    GPT_API_CLASS = GigaChatGPTAPI

    def start(self) -> ResponseMessage:
        arg0 = self.event.message.args[0] if self.event.message.args else None
        menu = [
            [["нарисуй", "draw"], self.menu_draw_image],
            [["препромпт", "препромт", "промпт", "preprompt", "prepromp", "prompt"], self.menu_preprompt],
            [['default'], self.default]
        ]
        method = self.handle_menu(menu, arg0)
        answer = method()
        return ResponseMessage(answer)

    def menu_draw_image(self, use_statistics=True) -> ResponseMessageItem:
        return super().menu_draw_image(use_statistics=False)

    def completions(self, messages, use_stats=True) -> ResponseMessageItem:
        return super().completions(messages, use_stats=False)

    def default(self, with_vision=True):
        return super().default(with_vision=False)
