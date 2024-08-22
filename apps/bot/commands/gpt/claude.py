from apps.bot.api.gpt.claudegptapi import ClaudeGPTAPI
from apps.bot.api.gpt.message import GPTMessages, ClaudeGPTMessages
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText, HelpTextItem
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.commands.abstract.gpt_command import GPTCommand
from apps.service.models import GPTPrePrompt


class Claude(GPTCommand):
    name = "claude"
    names = ["клауд"]
    access = Role.GPT
    abstract = False

    help_text = HelpText(
        commands_text="чат claude",
        help_texts=[
            HelpTextItem(
                access,
                GPTCommand.DEFAULT_HELP_TEXT_ITEMS + \
                [GPTCommand.VISION_HELP_TEXT_ITEM] + \
                GPTCommand.PREPROMPT_HELP_TEXT_ITEMS
            )
        ],
        extra_text=GPTCommand.DEFAULT_EXTRA_TEXT
    )

    def __init__(self):
        super().__init__(GPTPrePrompt.CLAUDE, ClaudeGPTAPI, ClaudeGPTMessages)

    def start(self) -> ResponseMessage:
        arg0 = self.event.message.args[0] if self.event.message.args else None
        menu = [
            [["препромпт", "препромт", "промпт", "preprompt", "prepromp", "prompt"], self.menu_preprompt],
            [['default'], self.default]
        ]
        method = self.handle_menu(menu, arg0)
        answer = method()
        return ResponseMessage(answer)

    def completions(self, messages: GPTMessages, use_statistics=True) -> ResponseMessageItem:
        return super().completions(messages, use_statistics=False)

    def default(self, with_vision=True):
        return super().default(with_vision=True)
