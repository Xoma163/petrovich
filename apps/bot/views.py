import json
from datetime import datetime

from django.http import JsonResponse, HttpResponse
from django.views import View

from apps.bot.api.github.issue import GithubIssueAPI
from apps.bot.classes.bots.api_bot import APIBot
from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.const.exceptions import PError
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.bot.mixins import CSRFExemptMixin


class APIView(CSRFExemptMixin, View):
    def post(self, request, *args, **kwargs):
        authorization = request.headers.get('Authorization')
        if not authorization:
            return JsonResponse({'error': 'no authorization header provided'}, status=500)
        if not authorization.startswith("Bearer "):
            return JsonResponse({'error': 'no bearer token in authorization header'}, status=500)
        if not request.POST and not request.body:
            return JsonResponse({'error': 'POST data is empty'}, status=500)
        if request.POST:
            data = request.POST
        else:
            data = json.loads(request.body.decode())
        text = data.get('text')
        if not text:
            return JsonResponse({'error': 'no text in POST data'}, status=500)

        query = {
            'text': text,
            'token': authorization.replace("Bearer ", '')
        }
        attachments = data.get('attachments')
        if attachments:
            query['attachments'] = attachments

        api_bot = APIBot()
        try:
            response = api_bot.parse(query)
        except PError as e:
            return JsonResponse({'error': str(e)}, status=500)
        except Exception:
            return JsonResponse({'wtf': True}, status=500)

        if not response:
            return JsonResponse({'wtf': True}, status=500)

        r_json = response.to_api()
        return JsonResponse(r_json, status=200)


class TelegramView(CSRFExemptMixin, View):
    def post(self, request, *args, **kwargs):
        raw = json.loads(request.body)
        tg_bot = TgBot()
        tg_bot.parse(raw)
        return HttpResponse(status=200)


class GithubView(CSRFExemptMixin, View):

    @staticmethod
    def send_notify_to_user(issue: GithubIssueAPI, text):
        if not issue.author:
            return
        user = issue.author.get_tg_user()
        bot = TgBot()
        rmi = ResponseMessageItem(text=text, peer_id=user.user_id)
        bot.send_response_message_item(rmi)

    def reopen_issue(self, issue: GithubIssueAPI):
        problem_str = TgBot.get_formatted_url('Проблема #' + str(issue.number), issue.remote_url)
        text = f"{problem_str} была переоткрыта"
        self.send_notify_to_user(issue, text)

    def closed_issue(self, issue: GithubIssueAPI):
        problem_str = TgBot.get_formatted_url('Проблема #' + str(issue.number), issue.remote_url)
        text = f"{problem_str} была закрыта"
        self.send_notify_to_user(issue, text)

    def delete_issue(self, issue: GithubIssueAPI):
        problem_str = TgBot.get_formatted_url('Проблема #' + str(issue.number), issue.remote_url)
        text = f"{problem_str} была удалена"
        self.send_notify_to_user(issue, text)

    def created_comment(self, data, issue: GithubIssueAPI):
        comment = data['comment']['body']
        problem_str = TgBot.get_formatted_url('проблемой #' + str(issue.number), issue.remote_url)
        text = f"Новый комментарий от разработчика под вашей {problem_str}\n\n{comment}"
        self.send_notify_to_user(issue, text)

    def new_label(self, data, issue: GithubIssueAPI):
        # Github при создании иши присылает вебхук, типа он пометил её label'ами. Такое скипаем
        if (datetime.utcnow() - issue.created_at).seconds < 10:
            return

        label_name = data['label']['name']
        problem_str = TgBot.get_formatted_url('проблемой #' + str(issue.number), issue.remote_url)
        text = f"Новый тег от разработчика под вашей {problem_str}\n\n{label_name}"
        self.send_notify_to_user(issue, text)

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
