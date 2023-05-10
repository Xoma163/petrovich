from django.urls import path

from petrovich.settings import env
from . import views

urlpatterns = [
    path(f'tg/{env.str("TG_TOKEN")}', views.TelegramView.as_view()),
    path('api', views.APIView.as_view()),
    path('github', views.GithubView.as_view())
]
