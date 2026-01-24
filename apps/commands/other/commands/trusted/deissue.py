from apps.bot.consts import Role
from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.commands.command import Command
from apps.commands.help_text import HelpTextItem, HelpText, HelpTextArgument
from apps.connectors.api.github.issue import GithubIssueAPI
from apps.shared.exceptions import PWarning


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
        answer = f"Проблема {_id} закрыта. "
        return ResponseMessage(ResponseMessageItem(text=answer))
