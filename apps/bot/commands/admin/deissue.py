from apps.bot.api.github import Github
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpTextItem, HelpText
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class DeIssue(Command):
    name = "деишю"
    names = ["хуишю"]

    help_text = HelpText(
        commands_text="закрывает проблему Петровича без решения",
        help_texts=[
            HelpTextItem(Role.ADMIN, [
                "(id) - закрывает проблему Петровича без решения"
            ])
        ]
    )

    args = 1
    non_mentioned = False
    access = Role.ADMIN

    def start(self) -> ResponseMessage:
        _id = self.event.message.args[0]
        github_api = Github()
        github_api.delete_issue(_id)
        answer = "Ишю закрыта"
        return ResponseMessage(ResponseMessageItem(text=answer))
