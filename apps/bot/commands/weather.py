from apps.bot.api.yandex.weather import YandexWeather
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.service.models import City


class Weather(Command):
    name = "погода"

    help_text = HelpText(
        commands_text="прогноз погоды",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand("[город=из профиля]", "прогноз погоды")
            ])
        ]
    )

    def start(self) -> ResponseMessage:
        if self.event.message.args:
            city = City.objects.filter(synonyms__icontains=self.event.message.args_str).first()
            if not city:
                raise PWarning("Не нашёл такой город")
        else:
            city = self.event.sender.city
        self.check_city(city)

        yandexweather_api = YandexWeather(log_filter=self.event.log_filter)
        answer = yandexweather_api.get_weather_str(city)
        return ResponseMessage(ResponseMessageItem(text=answer))
