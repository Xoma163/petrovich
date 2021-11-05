from django.urls import path

from . import views

urlpatterns = [
    path('yandex', views.yandex),
    path('api', views.APIView.as_view()),
]
