import json

from django.http import JsonResponse
# from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.bot.classes.bots.YandexBot import YandexBot

@csrf_exempt
def yandex(request):
    yb = YandexBot()
    print(json.loads(request.body))
    response_data = yb.parse(json.loads(request.body))
    print("response_data", response_data)
    return JsonResponse(response_data, status=200)


# @method_decorator(csrf_exempt, name='dispatch')
# class YandexBotView(View):
#     @csrf_exempt
#     def post(self, request, *args, **kwargs):
#         yb = YandexBot()
#         print(json.loads(request.body))
#         response_data = yb.parse(json.loads(request.body))
#         print("response_data", response_data)
#         return JsonResponse(response_data, status=200)
