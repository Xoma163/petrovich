import json

from django.http import JsonResponse, HttpResponse
# from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.bot.classes.bots.api.APIBot import APIBot
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.bots.vk.VkBot import VkBot
from apps.bot.classes.bots.yandex.YandexBot import YandexBot
from apps.bot.classes.consts.Exceptions import PError
from apps.bot.classes.mixins import CSRFExemptMixin
from petrovich.settings import env


@csrf_exempt
def yandex(request):
    yb = YandexBot()
    response_data = yb.parse(json.loads(request.body))
    return JsonResponse(response_data, status=200)


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


class VkView(CSRFExemptMixin, View):
    def post(self, request, *args, **kwargs):
        raw = json.loads(request.body)
        if raw['secret'] == env.str("VK_SECRET_KEY"):
            if raw['type'] == 'confirmation':
                return HttpResponse(env.str("VK_CONFIRMATION_TOKEN"), content_type="text/plain", status=200)
            else:
                vk_bot = VkBot()
                vk_bot.parse(raw)
                return HttpResponse('ok', content_type="text/plain", status=200)
