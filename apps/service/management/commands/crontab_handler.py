import threading
from datetime import datetime

from crontab import CronTab
from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.bot.utils.utils import localize_datetime
from petrovich.settings import TIME_ZONE


class Command(BaseCommand):

    def handle(self, *args, **options):
        schedule = [
            # Проверка на др
            ScheduleItem("0 10 * * *", "check_birthday"),
            # Проверка донатов
            ScheduleItem("*/30 * * * *", "check_donations", "46"),
            # Проверка оповещений
            ScheduleItem("*/1 * * * *", "check_notify"),
            # Проверка подписок
            ScheduleItem("*/30 * * * *", "check_subscribe"),
            # Отправка новостей Паше
            ScheduleItem("0 */6 * * *", "check_pasha_news", "130"),
            # Удаление сущностей которые должны быть удалены со временем
            ScheduleItem("0 9 * * *", "auto_delete"),
        ]

        dt_now = localize_datetime(datetime.utcnow(), TIME_ZONE).replace(second=0, microsecond=0)

        threads = []
        for item in schedule:
            # Берём прошедшие события но в пределах 1 минуты
            if item.cron.previous(dt_now) != -60:
                continue
            thread = threading.Thread(target=call_command, args=item.thread_args)
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()


class ScheduleItem:
    def __init__(self, cron: str, command: str, args: str = None, kwargs: dict = None):
        self.cron = CronTab(cron)
        self.command = command
        self.args = args
        self.kwargs = kwargs

    @property
    def thread_args(self):
        _args = [self.command]
        if self.args:
            _args.append(self.args)
        return _args
