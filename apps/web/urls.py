from django.urls import path

from . import views

urlpatterns = [
    path('', views.main_page),
    path('lana_translate/', views.lana_translate)
]
