import datetime

from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import localize_datetime
from apps.service.models import City


class Time(CommonCommand):
    names = ["время"]
    help_text = "Время - текущее время в городе"
    detail_help_text = "Время [город=из профиля] - текущее время в городе"

    def start(self):
        if self.event.args:
            city = City.objects.filter(synonyms__icontains=self.event.args[0]).first()
        else:
            city = self.event.sender.city
        self.check_city(city)

        new_date = localize_datetime(datetime.datetime.utcnow(), city.timezone.name)
        return new_date.strftime("%d.%m.%Y\n%H:%M:%S")
