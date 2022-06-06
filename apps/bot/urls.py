from django.urls import path

from petrovich.settings import env
from . import views

urlpatterns = [
    path(f'tg/{env.str("TG_TOKEN")}', views.TelegramView.as_view()),
    path(f'vk', views.VkView.as_view()),
    path('yandex', views.yandex),
    path('api', views.APIView.as_view()),
]
