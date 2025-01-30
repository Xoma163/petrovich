from apps.bot.api.github.issue import GithubIssueAPI
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextItem, HelpText, HelpTextArgument
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class DeIssue(Command):
    name = "деишю"
    names = ["хуишю"]

    help_text = HelpText(
        commands_text="закрывает проблему Петровича без решения",
        help_texts=[
            HelpTextItem(Role.TRUSTED, [
                HelpTextArgument("(id)", "закрывает проблему Петровича без решения")
            ])
        ]
    )

    args = 1
    access = Role.TRUSTED

    def start(self) -> ResponseMessage:
        _id = self.event.message.args[0]
        issue = GithubIssueAPI(log_filter=self.event.log_filter)
        issue.number = _id
        issue.get_from_github()

        if issue.author != self.event.sender and not self.event.sender.check_role(Role.ADMIN):
            raise PWarning("Вы не являетесь автором issue")

        issue.delete_in_github()
        answer = f"Проблема {_id}({issue.title}) закрыта. "
        return ResponseMessage(ResponseMessageItem(text=answer))
