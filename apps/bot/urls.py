from django.urls import path

from . import views

urlpatterns = [
    path('whereisme/', views.where_is_me),
]
