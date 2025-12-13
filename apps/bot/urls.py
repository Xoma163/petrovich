from django.urls import path

from . import views

urlpatterns = [
    path(f'tg-webhook', views.TelegramView.as_view()),
    path('api', views.APIView.as_view()),
    path('github', views.GithubView.as_view())
]
