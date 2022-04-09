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
    path('accounts/login/', views.CustomLoginView.as_view(), name="login"),
    path('lana_translate/', views.lana_translate),
    path('delivery_calculator/', views.DeliveryCalculatorTemplateView.as_view(), name='delivery_calculator'),
    path('camera/', views.CameraTemplateView.as_view(), name='camera'),
    path('calculator_session/', views.CalculatorSessionListView.as_view(), name='calculator_sessions'),
    path('calculator_session/<int:pk>', views.CalculatorSessionDetailView.as_view(), name='calculator_session'),
    path('calculator_session/api/calculator_session/<int:pk>/calculate/', calculate),
    path('calculator_session/api/', include(router.urls)),
    path('minecraft/skins/<str:name>', views.MinecraftSkin.as_view(), name='calculator_session'),
    path('minecraft/capes/<str:name>', views.MinecraftCape.as_view(), name='calculator_session'),
]
