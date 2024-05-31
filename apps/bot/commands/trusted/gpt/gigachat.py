from apps.bot.api.gpt.gigachatgptapi import GigachatGPTAPI
from apps.bot.api.gpt.gpt import GPTAPI
from apps.bot.api.gpt.message import GigachatGPTMessages, GPTMessages, GPTMessage
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText, HelpTextItem
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.commands.abstract.gpt_command import GPTCommand
from apps.service.models import GPTPrePrompt


class Gigachat(GPTCommand):
    name = "gigachat"
    names = ['гигачат', 'gigachad', 'гигачад']
    access = Role.TRUSTED
    abstract = False

    help_text = HelpText(
        commands_text="чат GigaChat",
        help_texts=[
            HelpTextItem(
                access,
                GPTCommand.DEFAULT_HELP_TEXT_ITEMS + \
                [GPTCommand.DRAW_HELP_TEXT_ITEM] + \
                GPTCommand.PREPROMPT_HELP_TEXT_ITEMS
            )
        ],
        extra_text=GPTCommand.DEFAULT_EXTRA_TEXT
    )

    GPT_PREPROMPT_PROVIDER: str = GPTPrePrompt.GIGACHAT
    GPT_API_CLASS: GPTAPI = GigachatGPTAPI
    GPT_MESSAGES: GPTMessage = GigachatGPTMessages

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

    def completions(self, messages: GPTMessages, use_statistics=True) -> ResponseMessageItem:
        return super().completions(messages, use_statistics=False)

    def default(self, with_vision=True):
        return super().default(with_vision=False)
