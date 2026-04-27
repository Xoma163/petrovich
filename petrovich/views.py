from django.http import HttpResponse
from django.views import View


class HealthcheckView(View):
    @staticmethod
    def get(request, *args, **kwargs):
        return HttpResponse("ok", status=200)
