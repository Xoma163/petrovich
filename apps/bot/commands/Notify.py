from datetime import datetime, timedelta

import dateutil
from dateutil import parser

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import WEEK_TRANSLATOR, Role, DELTA_WEEKDAY, Platform
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.utils import localize_datetime, normalize_datetime, remove_tz
from apps.service.models import Notify as NotifyModel


# Возвращает datetime, кол-во аргументов использованных для получения даты, была ли передана точная дата и время
def get_time(arg1, arg2, timezone=None):
    exact_datetime_flag = True
    if arg1 in DELTA_WEEKDAY:
        exact_datetime_flag = False
        arg1 = (datetime.today().date() + timedelta(days=DELTA_WEEKDAY[arg1])).strftime("%d.%m.%Y")

    if arg1 in WEEK_TRANSLATOR:
        exact_datetime_flag = False
        delta_days = WEEK_TRANSLATOR[arg1] - datetime.today().isoweekday()
        if delta_days <= 0:
            delta_days += 7
        arg1 = (datetime.today().date() + timedelta(days=delta_days)).strftime("%d.%m.%Y")

    default_datetime = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0)  # + timedelta(days=1)
    # ToDo: зачем? тут баг из-за которого время ебошится неправильно при завтра/послезавтра
    default_datetime = remove_tz(normalize_datetime(default_datetime, tz=timezone.name))
    try:
        if arg1.count('.') == 1:
            arg1 = f"{arg1}.{default_datetime.year}"
        date_str = f"{arg1} {arg2}"

        return parser.parse(date_str, default=default_datetime, dayfirst=True), 2, exact_datetime_flag
    except dateutil.parser._parser.ParserError:
        try:
            exact_datetime_flag = False
            return parser.parse(arg1, default=default_datetime, dayfirst=True), 1, exact_datetime_flag
        except dateutil.parser._parser.ParserError:
            return None, None, None


class Notify(Command):
    name = 'напомни'
    names = ["напомнить"]
    help_text = "напоминает о чём-либо"
    help_texts = [
        "(дата/дата и время/день недели) (сообщение/команда) - добавляет напоминание. Максимум можно добавить 5 напоминаний"
    ]
    args = 2
    platforms = [Platform.VK, Platform.TG]
    city = True

    def start(self):
        if not self.event.sender.check_role(Role.TRUSTED) and \
                len(NotifyModel.objects.filter(user=self.event.user)) >= 5:
            raise PWarning("Нельзя добавлять более 5 напоминаний")
        timezone = self.event.sender.city.timezone.name

        date, args_count, exact_time_flag = get_time(self.event.message.args[0], self.event.message.args[1],
                                                     self.event.sender.city.timezone)
        if args_count == 2:
            self.check_args(3)
        if not date:
            raise PWarning("Не смог распарсить дату")
        date = normalize_datetime(date, timezone)
        datetime_now = localize_datetime(datetime.utcnow(), "UTC")

        if (date - datetime_now).seconds < 60:
            raise PWarning("Нельзя добавлять напоминание на ближайшую минуту")
        if not exact_time_flag and ((date - datetime_now).days < 0 or (datetime_now - date).seconds < 0):
            date = date + timedelta(days=1)
        if (date - datetime_now).days < 0 or (datetime_now - date).seconds < 0:
            raise PWarning("Нельзя указывать дату в прошлом")

        text = self.event.message.args_str_case.split(' ', args_count)[args_count]
        if text[0] == '/':
            first_space = text.find(' ')
            if first_space > 0:
                command = text[1:first_space]
            else:
                command = text[1:]
            from apps.bot.commands.NotifyRepeat import NotifyRepeat
            if command in self.full_names or command in NotifyRepeat().full_names:
                text = f"/обосрать {self.event.sender.name}"
        notify_datetime = localize_datetime(remove_tz(date), timezone)

        notify = NotifyModel(date=date,
                             text=text,
                             user=self.event.user,
                             chat=self.event.chat,
                             text_for_filter=notify_datetime.strftime("%d.%m.%Y %H:%M") + " " + text)
        notify.save()
        notify.text_for_filter += f" ({notify.id})"
        notify.save()

        return f'Сохранил на дату {str(notify_datetime.strftime("%d.%m.%Y %H:%M"))}'
