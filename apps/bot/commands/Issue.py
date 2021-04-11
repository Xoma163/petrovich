from apps.bot.APIs.GithubAPI import GithubAPI
from apps.bot.classes.Consts import Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand


class Issue(CommonCommand):
    name = "баг"
    names = ["ошибка", "ишю", "ишью"]
    help_text = "добавляет проблему Петровича, которую нужно решить"
    help_texts = ["(текст/пересланные сообщения) - добавляет проблему Петровича, которую нужно решить"]
    platforms = [Platform.VK, Platform.TG]

    def start(self):
        msgs = self.event.fwd
        if not msgs:
            if not self.event.original_args:
                raise PWarning("Требуется аргументы или пересылаемые сообщения")

            msgs = [{'text': self.event.original_args, 'from_id': int(self.event.sender.user_id)}]

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
