from django.urls import path, include
from rest_framework import routers

from . import views
from .views import CalculatorProductViewSet, CalculatorSessionViewSet, calculate, CalculatorUserViewSet

app_name = 'web'

router = routers.DefaultRouter()
router.register(r'calculator_session', CalculatorSessionViewSet, basename='calculator_session')
router.register(r'calculator_product', CalculatorProductViewSet, basename='calculator_product')
router.register(r'calculator_user', CalculatorUserViewSet, basename='calculator_user')

urlpatterns = [
    path('', views.main_page),
    path('lana_translate/', views.lana_translate),
    path('delivery_calculator/', views.DeliveryCalculatorTemplateView.as_view(), name='delivery_calculator'),
    path('calculator_session/', views.CalculatorSessionListView.as_view(), name='calculator_sessions'),
    path('calculator_session/<int:pk>', views.CalculatorSessionDetailView.as_view(), name='calculator_session'),
    path('calculator_session/api/calculator_session/<int:pk>/calculate/', calculate),
    path('calculator_session/api/', include(router.urls)),
]
