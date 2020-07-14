import json

from django.core.management.base import BaseCommand

from apps.bot.APIs.YandexWeatherAPI import YandexWeatherAPI
from apps.service.models import City, Service


class Command(BaseCommand):

    def handle(self, *args, **options):
        cities = options['cities']
        for city_name in cities:
            city = City.objects.get(name__icontains=city_name)
            yandexweather_api = YandexWeatherAPI(city)
            weather_data = yandexweather_api.get_weather(False)
            weather_data_str = json.dumps(weather_data)

            entity_yesterday, _ = Service.objects.get_or_create(name=f'weatherchange_yesterday_{city.name}')
            entity_today, _ = Service.objects.get_or_create(name=f'weatherchange_today_{city.name}')
            entity_yesterday.value = entity_today.value
            entity_yesterday.save()
            entity_today.value = weather_data_str
            entity_today.save()

    def add_arguments(self, parser):
        parser.add_argument('cities', nargs='+', type=str, help='city')
