from apps.bot.APIs.GithubAPI import GithubAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform


class Issue(Command):
    name = "баг"
    names = ["ошибка", "ишю", "ишью"]
    help_text = "добавляет проблему Петровича, которую нужно решить"
    help_texts = ["(текст/пересланные сообщения) - добавляет проблему Петровича, которую нужно решить"]
    platforms = [Platform.VK, Platform.TG]
    args_or_fwd = 1

    def start(self):
        msgs = self.event.fwd
        if not msgs:
            msgs = [{'text': self.event.message.args_str, 'from_id': int(self.event.sender.user_id)}]

        issue_text = ""
        for msg in msgs:
            text = msg['text']
            if msg['from_id'] > 0:
                fwd_user = self.bot.get_user_by_id(msg['from_id'])
                username = str(fwd_user)
            else:
                username = str(self.bot.get_bot_by_id(msg['from_id']))
            issue_text += f"{username}:\n{text}\n\n"

        github_api = GithubAPI()
        title = f"Ишю от пользователя {self.event.sender}"
        body = f"{issue_text}\n\n" \
               f"Данное ишю сгенерировано автоматически"

        response = github_api.create_issue(title, body)
        result = {
            'msg': f"Сохранено\n"
                   f"Отслеживать созданное ишю можно по этой ссылке:\n"
                   f"{response['html_url']}",
            'attachments': [response['html_url']]
        }
        return result
