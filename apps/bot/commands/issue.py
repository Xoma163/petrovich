from django.contrib.auth.models import Group

from apps.bot.api.github.issue import GithubIssueAPI
from apps.bot.api.imgur import Imgur
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextItem, HelpText, HelpTextArgument
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.models import Profile


class Issue(Command):
    name = "баг"
    names = ["ошибка", "ишю", "ишью"]

    help_text = HelpText(
        commands_text="добавляет проблему Петровича, которую нужно решить",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextArgument(
                    "(проблема)\n[описание проблемы]\n[теги]",
                    "добавляет проблему Петровича"
                ),
                HelpTextArgument(
                    "(пересылаемое сообщение)",
                    "добавляет проблему Петровича"
                )
            ])
        ],
        extra_text=(
            "Возможные теги: #Баг #Фича #Говнокод #Документация #Тест #хелп\n\n"
            "Просьба по возможности указывать проблемы в следующем формате:\n"
            "[Название команды/сервиса] Краткое описание проблемы\n"
            "Описание проблемы в любом формате. Чем подробнее - тем лучше. Если есть логи и скриншоты - отлично\n"
            "Теги"
        )
    )

    args_or_fwd = True
    mentioned = True

    def start(self) -> ResponseMessage:
        if self.event.message.args:
            msg = self.event.message.raw.split(' ', 1)[1]
        elif self.event.message.quote:
            msg = self.event.message.quote
        elif self.event.fwd:
            msg = self.event.fwd[0].message.raw
        else:
            raise PWarning("В сообщении должны быть аргументы или пересылаемое сообщение")

        body = ""
        labels_in_github = []

        issue = GithubIssueAPI(log_filter=self.event.log_filter)

        if msg.count('\n') == 0:
            title = msg
        else:
            msg_split = msg.split('\n')
            title = msg_split[0]
            body = "\n".join(msg_split[1:-1])
            tags = self._get_tags(msg_split[-1])
            labels_in_github = [x for x in issue.get_all_labels() if x.lower() in tags] if tags else []
            if not labels_in_github:
                body = "\n".join(msg_split[1:])

        photos = self.event.get_all_attachments([PhotoAttachment])
        if photos:
            for photo in photos:
                i_api = Imgur(log_filter=self.event.log_filter)
                image_url = i_api.upload_image(photo.download_content())
                body += f"\n![image]({image_url})"
        body += f"\n\nИшю от пользователя {self.event.sender} (id={self.event.sender.pk})\n" \
                f"Данное ишю сгенерировано автоматически"
        body = body.lstrip("\n")

        issue.author = self.event.sender
        issue.title = title
        issue.body = body
        issue.assignee = GithubIssueAPI.REPO_OWNER
        issue.labels = labels_in_github
        issue.create_in_github()

        self.send_issue_info_to_admin(issue)

        answer = f"Отслеживать созданное ишю можно по {self.bot.get_formatted_url('ссылке', issue.remote_url)}"
        return ResponseMessage(ResponseMessageItem(text=answer))

    @staticmethod
    def _get_tags(text):
        tags = []
        if not text:
            return tags
        for x in text.split():
            if x.startswith("#"):
                tags.append(x[1:].lower().replace("_", " "))
        return tags

    def send_issue_info_to_admin(self, issue: GithubIssueAPI):

        admin_group = Group.objects.get(name=Role.ADMIN.name)
        profile = Profile.objects.filter(groups__in=[admin_group]).first()

        if profile == issue.author:
            return

        answer = f"Новая иша {self.bot.get_formatted_url('тут', issue.remote_url)}"
        rmi = ResponseMessageItem(answer)
        rmi.peer_id = profile.get_tg_user().user_id
        self.bot.send_response_message_item(rmi)
