from apps.bot.APIs.GithubAPI import GithubAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem


class DeIssue(Command):
    name = "деишю"
    names = ["хуишю"]
    help_text = "закрывает проблему Петровича без решения"
    help_texts = ["(id) - закрывает проблему Петровича без решения"]
    args = 1
    non_mentioned = False
    access = Role.ADMIN

    def start(self) -> ResponseMessage:
        _id = self.event.message.args[0]
        github_api = GithubAPI()
        github_api.delete_issue(_id)
        answer = "Ишю закрыта"
        return ResponseMessage(ResponseMessageItem(text=answer))
