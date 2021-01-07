from django.urls import path

from . import views

app_name = 'web'

urlpatterns = [
    path('', views.main_page),
    path('lana_translate/', views.lana_translate),
    path('calculator_session/', views.CalculatorSessionListView.as_view(), name='calculator_sessions'),
    path('calculator_session/<int:pk>', views.CalculatorSessionDetailView.as_view(), name='calculator_session')
]
