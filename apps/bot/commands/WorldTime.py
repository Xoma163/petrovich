import datetime
from itertools import groupby
from typing import List

from apps.bot.classes.command import Command
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import localize_datetime, remove_tz
from apps.service.models import City


class WorldTime(Command):
    name = "время"
    help_text = "текущее время в городе"
    help_texts = ["[город=из профиля] - текущее время в городе"]

    def start(self) -> ResponseMessage:
        # args
        if self.event.message.args:
            city_name = self.event.message.args[0]
            city = City.objects.filter(synonyms__icontains=city_name).first()
            if not city:
                raise PWarning(f"Не знаю такого города - {city_name}")
            answer = self._get_city_time_str(city)
        # pm
        elif self.event.is_from_pm:
            self.check_city()
            answer = self._get_city_time_str(self.event.sender.city)
        # chat
        else:
            dt_now = datetime.datetime.utcnow()
            cities = [x.city for x in self.event.chat.users.all() if x.city]
            if not cities:
                self.check_city()
                answer = self._get_city_time_str(self.event.sender.city)
            else:
                cities = sorted(cities, key=lambda x: self._group_key(dt_now, x))
                answers = []
                for _, items in groupby(cities, key=lambda x: self._group_key(dt_now, x)):
                    answers.append(self._get_cities_group_time_str(list(items)))
                answer = "\n".join(answers)

        return ResponseMessage(ResponseMessageItem(text=answer))

    # Господи помилуй эту сортировку
    @staticmethod
    def _group_key(dt_now, x):
        return remove_tz(localize_datetime(dt_now, x.timezone.name))

    @staticmethod
    def _get_city_time_str(city: City) -> str:
        new_date = localize_datetime(datetime.datetime.utcnow(), city.timezone.name)
        dt_str = new_date.strftime("%H:%M:%S")
        answer = f"{city} — {dt_str}"
        return answer

    def _get_cities_group_time_str(self, cities: List[City]) -> str:
        if len(cities) == 1:
            return self._get_city_time_str(cities[0])
        new_date = localize_datetime(datetime.datetime.utcnow(), cities[0].timezone.name)
        dt_str = new_date.strftime("%H:%M:%S")
        cities_str = ", ".join([x.name for x in cities])
        answer = f"{cities_str} — {dt_str}"
        return answer
