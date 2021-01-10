from django.core import serializers
from django.http import JsonResponse
from django.shortcuts import render
# Create your views here.
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from rest_framework.viewsets import ModelViewSet

from apps.web.models import CalculatorSession, CalculatorProduct
from apps.web.serializers import CalculatorProductSerializer, \
    CalculatorSessionSerializer, CalculatorSessionViewSerializer


def main_page(request):
    context = {}
    return render(request, 'base.html', context)


def lana_translate(request):
    return render(request, 'lana_translate.html')


class CalculatorSessionListView(ListView):
    model = CalculatorSession


class CalculatorSessionDetailView(DetailView):
    model = CalculatorSession


def get_calculator_session(request, pk):
    session = CalculatorSession.objects.get(pk=pk)
    session_json = serializers.serialize('json', [session])
    return JsonResponse({'session': session_json})


class CalculatorProductViewSet(ModelViewSet):
    queryset = CalculatorProduct.objects.all()
    serializer_class = CalculatorProductSerializer

    def get_queryset(self):
        """
        This view should return a list of all the purchases
        for the currently authenticated user.
        """

        _filter = {}
        session = self.request.GET.get('session', 0)
        if session:
            _filter['calculatorsession'] = session
        return self.queryset.filter(**_filter)


class CalculatorSessionViewSet(ModelViewSet):
    queryset = CalculatorSession.objects.all()
    serializer_class = CalculatorSessionSerializer

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return CalculatorSessionViewSerializer
        return CalculatorSessionSerializer

    def retrieve(self, request, *args, **kwargs):
        result = super().retrieve(request, *args, **kwargs)
        result.data['uom_list'] = [{'label': x.label, 'value': x.value} for x in CalculatorProduct.UnitOfMeasurement]

        return result


def calculate(request, pk):
    session = CalculatorSession.objects.get(pk=pk)
    return JsonResponse({'data': session.calculate()}, status=200)
