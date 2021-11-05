from apps.bot.APIs.GithubAPI import GithubAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from apps.bot.utils.utils import get_tg_formatted_url


class Issue(Command):
    name = "баг"
    names = ["ошибка", "ишю", "ишью"]
    help_text = "добавляет проблему Петровича, которую нужно решить"
    help_texts = ["(текст) - добавляет проблему Петровича, которую нужно решить"]
    args = 1

    def start(self):
        text = self.event.message.args_str_case
        username = str(self.event.sender)
        issue_text = f"{username}:\n{text}\n\n"

        github_api = GithubAPI()
        title = f"Ишю от пользователя {self.event.sender}"
        body = f"{issue_text}\n\n" \
               f"Данное ишю сгенерировано автоматически"

        response = github_api.create_issue(title, body)
        if self.event.platform == Platform.TG:
            text = f"Сохранено\nОтслеживать созданное ишю можно по {get_tg_formatted_url('ишю', response['html_url'])} ссылке:\n",
        else:
            text = f"Сохранено\n" \
                   f"Отслеживать созданное ишю можно по этой ссылке:\n" \
                   f"{response['html_url']}"
        return text
