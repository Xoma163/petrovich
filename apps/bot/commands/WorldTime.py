import datetime
import re
from itertools import groupby
from typing import List

from apps.bot.classes.command import Command
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.event.event import Event
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import localize_datetime, remove_tz, normalize_datetime
from apps.service.models import City


class WorldTime(Command):
    name = "время"
    help_text = "текущее время в городе"
    help_texts = ["[город=из профиля] - текущее время в городе"]

    help_texts_extra = \
        "Если в сообщении будет указание времени, а у пользователя будет проставлен город в профиле, то бот автоматически проставит соответствующее время для остальных городов в чате"

    @staticmethod
    def accept_extra(event: Event) -> bool:
        if not event.chat:
            return False

        if not event.message or not event.message.raw:
            return False

        if not event.sender or not event.sender.city:
            return False

        r = re.compile(r"(^|\D)(\d\d[:.]\d\d)($|\D)")
        return bool(r.findall(event.message.raw))

    def start(self) -> ResponseMessage:
        # args

        r = re.compile(r"(^|\D)(\d\d[:.]\d\d)($|\D)")
        if res := r.findall(self.event.message.raw):
            new_res = []
            for item in res:
                h, m = re.split('[:.]', item[1])
                if int(h) > 24 or int(m) > 60:
                    continue
                new_res.append(f"{h}:{m}")
            new_res = list(set(new_res))
            return self._get_time_in_cities_in_text(new_res)
        if self.event.message.args:
            city_name = self.event.message.args[0]
            city = City.objects.filter(synonyms__icontains=city_name).first()
            if not city:
                raise PWarning(f"Не знаю такого города - {city_name}")
            answer = self._get_city_time_str(city, "%H:%M:%S")
        # pm
        elif self.event.is_from_pm:
            self.check_city()
            answer = self._get_city_time_str(self.event.sender.city, "%H:%M:%S")
        # chat
        else:
            dt_now = datetime.datetime.utcnow()
            answer = self._get_time_in_cities(dt_now, "%H:%M:%S")

        return ResponseMessage(ResponseMessageItem(text=answer))

    def _get_time_in_cities_in_text(self, times_str):
        answer = []
        for item in times_str:
            dt = datetime.datetime.strptime(item, "%H:%M")
            dt = datetime.datetime.utcnow().replace(hour=dt.hour, minute=dt.minute)
            dt = remove_tz(normalize_datetime(dt, self.event.sender.city.timezone.name))
            time_in_cities = self._get_time_in_cities(dt, "%H:%M")
            answer.append(f"{item}\n{time_in_cities}")
        answer = "\n\n".join(answer)
        return ResponseMessage(ResponseMessageItem(text=answer, reply_to=self.event.message.id))

    def _get_time_in_cities(self, dt: datetime.datetime, strf_format):
        cities = set([x.city for x in self.event.chat.users.all() if x.city])
        if not cities:
            self.check_city()
            return self._get_city_time_str(self.event.sender.city, strf_format)
        else:
            cities = sorted(cities, key=lambda x: self._group_key(dt, x))
            answers = []
            for _, items in groupby(cities, key=lambda x: self._group_key(dt, x)):
                answers.append(self._get_cities_group_time_str(list(items), dt, strf_format))
            return "\n".join(answers)

    # Господи помилуй эту сортировку
    @staticmethod
    def _group_key(dt_now, x):
        return remove_tz(localize_datetime(dt_now, x.timezone.name))

    @staticmethod
    def _get_city_time_str(city: City, strf_format=None, dt=None) -> str:
        if not dt:
            dt = datetime.datetime.utcnow()
        new_date = localize_datetime(dt, city.timezone.name)
        dt_str = new_date.strftime(strf_format)
        answer = f"{city} — {dt_str}"
        return answer

    def _get_cities_group_time_str(self, cities: List[City], dt, strf_format) -> str:
        if len(cities) == 1:
            return self._get_city_time_str(cities[0], strf_format, dt)
        new_date = localize_datetime(dt, cities[0].timezone.name)
        dt_str = new_date.strftime(strf_format)
        cities_str = ", ".join([x.name for x in cities])
        answer = f"{cities_str} — {dt_str}"
        return answer
