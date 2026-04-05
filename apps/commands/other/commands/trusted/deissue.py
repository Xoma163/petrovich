import re

from apps.bot.consts import RoleEnum
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
            HelpTextItem(RoleEnum.TRUSTED, [HelpTextArgument("(id)", "закрывает проблему Петровича без решения")])
        ],
    )

    # args = 1
    access = RoleEnum.TRUSTED

    def start(self) -> ResponseMessage:
        issue_id = None
        if self.event.fwd:
            try:
                url = self.event.fwd[0].message.entities[0]["url"]
                m = re.search(r"/issues/(\d+)$", url)
                issue_id = m.group(1) if m else None
            except Exception:
                PWarning("Не смог распарсить присланное сообщение")
        elif self.event.message.args:
            self.int_args = [0]
            self.parse_int()
            issue_id = self.event.message.args[0]

        else:
            raise PWarning("Передайте id иши в аргументах или перешлите сообщение с созданной ишой")
        issue = GithubIssueAPI(log_filter=self.event.log_filter)
        issue.number = issue_id
        issue.get_from_github()

        if issue.author != self.event.sender and not self.event.sender.check_role(RoleEnum.ADMIN):
            raise PWarning("Вы не являетесь автором issue")

        issue.delete_in_github()
        answer = f"Проблема {issue_id} закрыта. "
        return ResponseMessage(ResponseMessageItem(text=answer))
