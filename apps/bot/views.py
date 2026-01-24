import datetime
import json
import re

from django.http import HttpResponse
from django.views import View

from apps.bot.core.bot.tg_bot.tg_bot import TgBot
from apps.bot.core.messages.attachments.photo import PhotoAttachment
from apps.bot.core.messages.response_message import ResponseMessageItem
from apps.bot.utils.utils import get_admin_profile
from apps.connectors.api.github.issue import GithubIssueAPI
from apps.shared.mixins import CSRFExemptMixin
from petrovich.settings import env


class TelegramView(CSRFExemptMixin, View):
    @staticmethod
    def post(request, *args, **kwargs):
        if env.str('TG_WEBHOOK_SECRET') and \
                request.headers.get('x-telegram-bot-api-secret-token') != env.str('TG_WEBHOOK_SECRET'):
            return HttpResponse(status=403)
        raw = json.loads(request.body)
        tg_bot = TgBot()
        tg_bot.parse(raw)
        return HttpResponse(status=200)


class GithubView(CSRFExemptMixin, View):
    NEW_COMMENT_FROM_DEVELOPER_TEMPLATE = "Новый комментарий от разработчика под вашей {problem_str}\n\n{comment}\n\nЧтобы оставить комментарий, ответьте на это сообщение"
    AUTO_GENERATED_COMMENT_STR = "Данный комментарий сгенерирован автоматически"

    @staticmethod
    def send_notify_to_user(issue: GithubIssueAPI, text, attachments=None):
        user_profile = issue.author
        if not user_profile:
            return

        admin_profile = get_admin_profile()
        if user_profile == admin_profile:
            return

        user = user_profile.get_tg_user()
        bot = TgBot()
        rmi = ResponseMessageItem(text=text, peer_id=user.user_id, attachments=attachments)
        bot.send_response_message_item(rmi)

    def reopen_issue(self, issue: GithubIssueAPI):
        problem_str = TgBot.get_formatted_url('Проблема #' + str(issue.number), issue.remote_url)
        text = f"{problem_str} была переоткрыта"
        self.send_notify_to_user(issue, text)

    def closed_issue(self, issue: GithubIssueAPI):
        problem_str = TgBot.get_formatted_url('Проблема #' + str(issue.number), issue.remote_url)
        text = f"{problem_str} была закрыта"
        if issue.state_reason_is_not_planned:
            text += " как незапланированная"
        self.send_notify_to_user(issue, text)

    def delete_issue(self, issue: GithubIssueAPI):
        problem_str = TgBot.get_formatted_url('Проблема #' + str(issue.number), issue.remote_url)
        text = f"{problem_str} была удалена"
        self.send_notify_to_user(issue, text)

    def created_comment(self, data, issue: GithubIssueAPI):
        comment = data['comment']['body']
        if self.AUTO_GENERATED_COMMENT_STR in data['comment']['body']:
            return

        photo_attachments, comment = self._get_image_urls_from_text(comment)

        problem_str = TgBot.get_formatted_url('проблемой #' + str(issue.number), issue.remote_url)
        answer = self.NEW_COMMENT_FROM_DEVELOPER_TEMPLATE.format(problem_str=problem_str, comment=comment)
        self.send_notify_to_user(issue, answer, attachments=photo_attachments)

    def new_label(self, data, issue: GithubIssueAPI):
        # Github при создании иши присылает вебхук, типа он пометил её label'ами. Такое скипаем
        if (datetime.datetime.now(datetime.UTC) - issue.created_at).seconds < 10:
            return

        label_name = data['label']['name']
        problem_str = TgBot.get_formatted_url('проблемой #' + str(issue.number), issue.remote_url)
        text = f"Новый тег от разработчика под вашей {problem_str}\n\n{label_name}"
        self.send_notify_to_user(issue, text)

    @staticmethod
    def _get_image_urls_from_text(comment: str) -> tuple[list[PhotoAttachment] | None, str]:
        IMG_RE = r"<img\b[^>]*\bsrc\s*=\s*\"(.*)[\"']\s*\/>"
        image_urls = re.findall(IMG_RE, comment)
        if not image_urls:
            return None, comment
        photo_attachments = []
        for image_url in image_urls:
            pa = PhotoAttachment()
            pa.public_download_url = image_url
            photo_attachments.append(pa)
        comment = re.sub(IMG_RE, '', comment, flags=re.I)
        return photo_attachments, comment

    def post(self, request):
        data = json.loads(request.body)
        issue = GithubIssueAPI()
        issue.parse_response(data['issue'])

        if data['action'] == 'closed':
            self.closed_issue(issue)
        elif data['action'] == 'reopened':
            self.reopen_issue(issue)
        elif data['action'] == 'deleted':
            self.delete_issue(issue)
        elif data['action'] == 'created' and \
                data.get('comment') and \
                data['comment']['user']['id'] == data['issue']['user']['id']:
            self.created_comment(data, issue)
        elif data['action'] == 'labeled':
            self.new_label(data, issue)
        return HttpResponse('ok', status=200)
