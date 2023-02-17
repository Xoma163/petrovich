from apps.bot.APIs.GithubAPI import GithubAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.bots.Bot import upload_image_to_vk_server
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.utils.utils import get_tg_formatted_url


class Issue(Command):
    name = "баг"
    names = ["ошибка", "ишю", "ишью"]
    help_text = "добавляет проблему Петровича, которую нужно решить"
    help_texts = ["(проблема)\\n[описание проблема]\\n[теги] - добавляет проблему Петровича, которую нужно решить"]
    help_texts_extra = "Возможные теги: #Баг #Фича #Говнокод #Документация #Тест #Заливка_мемов_на_канал #хелп"
    args = 1
    mentioned = True

    def start(self):
        msg = self.event.message.args_str_case

        body = ""
        tags = ""

        if msg.count('\n') == 0:
            title = msg
        elif msg.count('\n') == 1:
            msg_split = msg.split('\n')
            title, body = msg_split
        else:
            msg_split = msg.split('\n')
            title = msg_split[0]
            body = "\n".join(msg_split[1:-1])
            tags = msg_split[-1]
        photos = self.event.get_all_attachments([PhotoAttachment])
        if photos:
            photo = photos[0]
            image_url = upload_image_to_vk_server(photo.download_content())
            body += f"\n![image]({image_url})"
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
