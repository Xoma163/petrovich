from apps.bot.APIs.GithubAPI import GithubAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from apps.bot.utils.utils import get_tg_formatted_url


class Issue(Command):
    name = "баг"
    names = ["ошибка", "ишю", "ишью"]
    help_text = "добавляет проблему Петровича, которую нужно решить"
    help_texts = ["(проблема)\\n[описание проблема]\\n[теги] - добавляет проблему Петровича, которую нужно решить"]
    help_texts_extra = "Возможные теги: #Баг #Фича #Говнокод #Документация #Тест #Заливка_мемов_на_канал #хелп"
    args = 1
    non_mentioned = False

    def start(self):
        msg = self.event.message.args_str_case

        body = ""
        tags = ""

        if msg.count('\n') == 0:
            title = msg
        elif msg.count('\n') == 1:
            title, body = msg.split('\n')
        else:
            title, body, tags = msg.split('\n', 3)

        body += f"\n\nИшю от пользователя {self.event.sender} (id={self.event.sender.pk})\n" \
                f"Данное ишю сгенерировано автоматически"

        tags = [
            x[1:].lower().replace("_", " ") if x.startswith("#") else x.lower().replace("_", " ")
            for x in tags.split(" ") if x
        ] if tags else []

        github_api = GithubAPI()
        labels_in_github = [x for x in github_api.get_all_labels() if x.lower() in tags] if tags else []

        response = github_api.create_issue(title, body, GithubAPI.REPO_OWNER, labels=labels_in_github)
        if self.event.platform == Platform.TG:
            text = f"Отслеживать созданное ишю можно по {get_tg_formatted_url('ссылке', response['html_url'])}"
        else:
            text = f"Отслеживать созданное ишю можно по ссылке:\n" \
                   f"{response['html_url']}"
        return text
