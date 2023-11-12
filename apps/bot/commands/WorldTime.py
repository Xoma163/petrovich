import datetime
from collections import Counter

from apps.bot.classes.command import Command
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import localize_datetime
from apps.service.models import City


class WorldTime(Command):
    name = "время"
    help_text = "текущее время в городе"
    help_texts = ["[город=из профиля] - текущее время в городе"]

    def start(self) -> ResponseMessage:
        # args
        if self.event.message.args:
            city = City.objects.filter(synonyms__icontains=self.event.message.args[0]).first()
            answer = self._get_city_time_str(city)
        # pm
        elif self.event.is_from_pm:
            self.check_city()
            answer = self._get_city_time_str(self.event.sender.city)
        # chat
        else:
            cities = [x.city for x in self.event.chat.users.all() if x.city]
            x = Counter(cities)
            answers = []
            for city, _ in x.most_common():
                answers.append(self._get_city_time_str(city))
            answer = "\n".join(answers)

        return ResponseMessage(ResponseMessageItem(text=answer))

    @staticmethod
    def _get_city_time_str(city: City) -> str:
        new_date = localize_datetime(datetime.datetime.utcnow(), city.timezone.name)
        dt_str = new_date.strftime("%H:%M:%S")
        answer = f"Время в городе {city} — {dt_str}"
        return answer
