import datetime
import re
from itertools import groupby
from typing import Iterable

from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning, PSkip
from apps.bot.classes.event.event import Event
from apps.bot.classes.help_text import HelpTextItem, HelpText, HelpTextArgument
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import localize_datetime, remove_tz, normalize_datetime
from apps.service.models import City


class Time(Command):
    name = "время"

    help_text = HelpText(
        commands_text="текущее время в городе",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextArgument("[город=из профиля]", "текущее время в городе")
            ])
        ],
        extra_text=(
            "Если в сообщении будет указание времени, а у пользователя будет проставлен город в профиле, то бот "
            "автоматически проставит соответствующее время для остальных городов в чате"
        )
    )

    priority = -5

    REGEXP = r"(^|\D)(\d?\d:\d\d)($|\D)"

    def accept(self, event: Event) -> bool:
        super_res = super().accept(event)
        if not event.chat:
            return super_res

        if not event.message or not event.message.raw:
            return super_res

        if not event.sender or not event.sender.city:
            return super_res

        r = re.compile(self.REGEXP)
        res = bool(r.findall(event.message.raw))
        if res:
            return True
        return super_res

    def start(self) -> ResponseMessage:
        # time in message
        r = re.compile(self.REGEXP)
        if res := r.findall(self.event.message.raw):
            if not self.event.chat.settings.time_conversion:
                raise PSkip()
            new_res = []
            for item in res:
                h, m = re.split('[:.]', item[1])
                if int(h) > 24 or int(m) > 60:
                    continue
                new_res.append(f"{h}:{m}")
            new_res = list(set(new_res))
            return self._get_time_in_cities_in_text(new_res)
        # command + arg
        if self.event.message.args:
            city_name = self.event.message.args[0]
            city = City.objects.filter(synonyms__icontains=city_name).first()
            if not city:
                raise PWarning(f"Не знаю такого города - {city_name}")
            answer = self._get_city_time_str(city, "%H:%M:%S")
        # pm command
        elif self.event.is_from_pm:
            self.check_city()
            answer = self._get_city_time_str(self.event.sender.city, "%H:%M:%S")
        # chat command
        else:
            dt_now = datetime.datetime.utcnow()
            cities = self.get_cities_in_chat()
            answer = self._get_time_in_cities(dt_now, "%H:%M:%S", cities)

        return ResponseMessage(ResponseMessageItem(text=answer))

    def _get_time_in_cities_in_text(self, times_str):
        answer = []
        cities = self.get_cities_in_chat()
        if len(cities) < 2:
            raise PSkip()

        _dt = datetime.datetime.strptime(times_str[0], "%H:%M")
        timezones_count = len(list(self.group_cities(cities, _dt)))
        if timezones_count < 2:
            raise PSkip()

        for item in times_str:
            dt = datetime.datetime.strptime(item, "%H:%M")
            dt = datetime.datetime.utcnow().replace(hour=dt.hour, minute=dt.minute)
            dt = remove_tz(normalize_datetime(dt, self.event.sender.city.timezone.name))
            time_in_cities = self._get_time_in_cities(dt, "%H:%M", cities)
            answer.append(f"{item}\n{time_in_cities}")
        answer = "\n\n".join(answer)
        return ResponseMessage(ResponseMessageItem(text=answer, reply_to=self.event.message.id))

    def _get_time_in_cities(self, dt: datetime.datetime, strf_format, cities: set[City]):
        if not cities:
            self.check_city()
            return self._get_city_time_str(self.event.sender.city, strf_format)
        else:
            cities = sorted(cities, key=lambda x: self._group_key(dt, x))
            answers = []
            for _, items in self.group_cities(cities, dt):
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

    def _get_cities_group_time_str(self, cities: list[City], dt, strf_format) -> str:
        if len(cities) == 1:
            return self._get_city_time_str(cities[0], strf_format, dt)
        new_date = localize_datetime(dt, cities[0].timezone.name)
        dt_str = new_date.strftime(strf_format)
        cities_str = ", ".join([x.name for x in cities])
        answer = f"{cities_str} — {dt_str}"
        return answer

    def get_cities_in_chat(self) -> set[City]:
        return set([x.city for x in self.event.chat.users.all() if x.city])

    def group_cities(self, cities: Iterable[City], dt: datetime.datetime):
        return groupby(cities, key=lambda x: self._group_key(dt, x))
