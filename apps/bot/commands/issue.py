from apps.bot.api.github import Github
from apps.bot.api.imgur import Imgur
from apps.bot.classes.command import Command
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Issue(Command):
    name = "баг"
    names = ["ошибка", "ишю", "ишью"]
    help_text = "добавляет проблему Петровича, которую нужно решить"
    help_texts = ["(проблема)\\n[описание проблема]\\n[теги] - добавляет проблему Петровича, которую нужно решить"]
    help_texts_extra = "Возможные теги: #Баг #Фича #Говнокод #Документация #Тест #Заливка_мемов_на_канал #хелп"
    args = 1
    mentioned = True

    def start(self) -> ResponseMessage:
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
            for photo in photos:
                i_api = Imgur()
                image_url = i_api.upload_image(photo.download_content())
                body += f"\n![image]({image_url})"
        body += f"\n\nИшю от пользователя {self.event.sender} (id={self.event.sender.pk})\n" \
                f"Данное ишю сгенерировано автоматически"

        tags = [
            x[1:].lower().replace("_", " ") if x.startswith("#") else x.lower().replace("_", " ")
            for x in tags.split(" ") if x
        ] if tags else []

        github_api = Github()
        labels_in_github = [x for x in github_api.get_all_labels() if x.lower() in tags] if tags else []

        r = github_api.create_issue(title, body, Github.REPO_OWNER, labels=labels_in_github)
        answer = f"Отслеживать созданное ишю можно по {self.bot.get_formatted_url('ссылке', r['html_url'])}"

        return ResponseMessage(ResponseMessageItem(text=answer))
