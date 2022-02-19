import json

from django.http import JsonResponse
# from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.bot.classes.bots.api.APIBot import APIBot
from apps.bot.classes.bots.yandex.YandexBot import YandexBot
from apps.bot.classes.consts.Exceptions import PError
from apps.bot.classes.mixins import CSRFExemptMixin


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

        req = json.loads(request.body)
        text = req.get('text')
        if not text:
            return JsonResponse({'error': 'no text in query'}, status=500)

        attachments = req.get('attachments')
        query = {
            'text': text,
            'token': authorization.replace("Bearer ", '')
        }
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
