from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.attachments.poll import PollAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Poll(Command):
    name = "опрос"
    args = 2
    help_text = HelpText(
        commands_text="создать опрос",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand("(вопрос)\n(вариант ответа 1)\n(вариант ответа 2)\n[вариант ответа 3]...",
                                    "создаёт опрос"),
            ])
        ],
        extra_text="Должен быть передан вопрос и как минимум 2 варианта ответов"
    )

    def start(self) -> ResponseMessage:
        question, *options = self.event.message.args_str_case.split('\n')
        if len(options) == 0:
            raise PWarning("Не переданы варианты ответов")
        if len(options) == 1:
            raise PWarning("Должно быть хотя бы 2 варианта ответов")
        poll = PollAttachment()
        poll.question = question
        poll.options = options
        return ResponseMessage(ResponseMessageItem(attachments=[poll]))
