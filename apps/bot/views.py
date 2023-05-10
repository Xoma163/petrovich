import json
import re

from django.http import JsonResponse, HttpResponse
from django.views import View

from apps.bot.classes.bots.api.APIBot import APIBot
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.consts.Exceptions import PError
from apps.bot.mixins import CSRFExemptMixin
from apps.bot.models import Profile


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

    def send_notify_to_user(self, data, text):
        issue = data['issue']
        issue_body = issue['body']
        r = re.compile(r"Ишю от пользователя .* \(id=(.*)\)")
        match = r.findall(issue_body)
        if not match:
            return HttpResponse('ok', status=200)
        profile_pk = match[-1]
        profile = Profile.objects.get(pk=profile_pk)
        user = profile.get_tg_user()
        bot = TgBot()
        bot.parse_and_send_msgs(text, user.peer_id)

    def closed_issue(self, data):
        issue = data['issue']

        not_fixed = any(x['name'] for x in issue['labels'] if x['name'] == 'Не пофикшу')
        if not_fixed:
            text = f"Проблема была закрыта с меткой \"Не пофикшу\"\n{issue['html_url']}"
        else:
            text = f"Проблема была закрыта\n{issue['html_url']}"
        self.send_notify_to_user(data, text)

    def created_comment(self, data):
        issue = data['issue']
        comment = data['comment']['body']
        text = f"Новый комментарий от разработчика под вашей проблемой\n{issue['html_url']}\n\n{comment}"
        self.send_notify_to_user(data, text)

    def post(self, request):
        data = json.loads(request.body)
        if data['action'] == 'closed':
            self.closed_issue(data)
        elif data['action'] == 'created' and 'comment' in data and data['comment']['user']['id'] == \
                data['issue']['user']['id']:
            self.created_comment(data)
        return HttpResponse('ok', status=200)
