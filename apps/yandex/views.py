# Create your views here.
import json

from django.views.decorators.csrf import csrf_exempt


# from apps.bot.classes.bots.YandexBot import YandexBot


@csrf_exempt
def yandex(request):
    # yb = YandexBot()
    print(json.loads(request.body))
    # response_data = yb.parse(json.loads(request.body))
    # print("response_data", response_data)
    # return JsonResponse(response_data, status=200)
