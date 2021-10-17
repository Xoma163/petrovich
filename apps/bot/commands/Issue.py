from apps.bot.APIs.GithubAPI import GithubAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform


class Issue(Command):
    name = "баг"
    names = ["ошибка", "ишю", "ишью"]
    help_text = "добавляет проблему Петровича, которую нужно решить"
    help_texts = ["(текст) - добавляет проблему Петровича, которую нужно решить"]
    platforms = [Platform.VK, Platform.TG]
    args = 1

    def start(self):
        text = self.event.message.args_str
        username = str(self.event.sender)
        issue_text = f"{username}:\n{text}\n\n"

        github_api = GithubAPI()
        title = f"Ишю от пользователя {self.event.sender}"
        body = f"{issue_text}\n\n" \
               f"Данное ишю сгенерировано автоматически"

        response = github_api.create_issue(title, body)
        result = {
            'text': f"Сохранено\n"
                   f"Отслеживать созданное ишю можно по этой ссылке:\n"
                   f"{response['html_url']}",
            'attachments': [response['html_url']]
        }
        return result
