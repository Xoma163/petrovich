import json
from django.core import serializers
from django.http import JsonResponse
from django.shortcuts import render
# Create your views here.
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from apps.web.models import CalculatorSession, CalculatorProduct
from apps.web.serializers import serialize


def main_page(request):
    context = {}
    return render(request, 'base.html', context)


def lana_translate(request):
    return render(request, 'lana_translate.html')


# def get_calculator_sessions(request):
#     sessions = CalculatorSession.objects.all()
#     sessions_json = serializers.serialize('json', sessions)
#     return JsonResponse({'sessions': sessions_json})

class CalculatorSessionListView(ListView):
    model = CalculatorSession


class CalculatorSessionDetailView(DetailView):
    model = CalculatorSession

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        # context_data['object_json'] = serialize('json', [context_data['object']])
        context_data['object_json'] = serialize(context_data['object'])
        context_data['uom_list'] = json.dumps([{'label':x.label, 'value':x.value} for x in CalculatorProduct.UnitOfMeasurement])
        return context_data


def get_calculator_session(request, pk):
    session = CalculatorSession.objects.get(pk=pk)
    session_json = serializers.serialize('json', [session])
    return JsonResponse({'session': session_json})
