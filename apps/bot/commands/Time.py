import datetime

from apps.bot.classes.Command import Command
from apps.bot.utils.utils import localize_datetime
from apps.service.models import City


class Time(Command):
    name = "время"
    help_text = "текущее время в городе"
    help_texts = ["[город=из профиля] - текущее время в городе"]

    def start(self):
        city = None
        if self.event.message.args:
            city = City.objects.filter(synonyms__icontains=self.event.message.args[0]).first()
        if not city:
            city = self.event.sender.city
        self.check_city(city)

        new_date = localize_datetime(datetime.datetime.utcnow(), city.timezone.name)
        dt_str = new_date.strftime("%d.%m.%Y\n%H:%M:%S")
        return f"Время в городе {city}\n\n{dt_str}"
