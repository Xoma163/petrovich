from apps.bot.APIs.YandexWeatherAPI import YandexWeatherAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem
from apps.service.models import City


class Weather(Command):
    name = "погода"
    name_tg = "weather"
    help_text = "прогноз погоды"
    help_texts = [
        "[город=из профиля] - прогноз погоды"
    ]

    def start(self) -> ResponseMessage:
        if self.event.message.args:
            city = City.objects.filter(synonyms__icontains=self.event.message.args_str).first()
            if not city:
                raise PWarning("Не нашёл такой город")
        else:
            city = self.event.sender.city
        self.check_city(city)

        yandexweather_api = YandexWeatherAPI()
        answer = yandexweather_api.get_weather_str(city)
        return ResponseMessage(ResponseMessageItem(text=answer))
