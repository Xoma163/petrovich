from django.http import JsonResponse
from django.views import View


class HealthcheckView(View):
    @staticmethod
    def get(request, *args, **kwargs):
        return JsonResponse({"status": "ok"}, status=200)
