from django.urls import path

from . import views

urlpatterns = [
    path('tg-webhook', views.TelegramView.as_view()),
    path('github', views.GithubView.as_view())
]
