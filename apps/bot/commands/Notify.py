from datetime import datetime, timedelta

from dateutil import parser
from dateutil.parser import ParserError

from apps.bot.classes.Command import Command
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.utils import localize_datetime, normalize_datetime, remove_tz
from apps.service.models import Notify as NotifyModel

DELTA_WEEKDAY = {
    'сегодня': 0,
    'завтра': 1,
    'послезавтра': 2,
}

WEEK_TRANSLATOR = {
    'понедельник': 1, 'пн': 1,
    'вторник': 2, 'вт': 2,
    'среда': 3, 'ср': 3,
    'четверг': 4, 'чт': 4,
    'пятница': 5, 'пт': 5,
    'суббота': 6, 'сб': 6,
    'воскресенье': 7, 'воскресение': 7, 'вс': 7,
}


class Notify(Command):
    name = 'напомни'
    names = ["напомнить"]
    help_text = "напоминает о чём-либо"
    help_texts = [
        "(дата/дата и время/день недели) (сообщение/команда/вложения) - добавляет напоминание. Максимум можно добавить 5 напоминаний"
    ]
    args = 1
    platforms = [Platform.TG]
    city = True

    bot: TgBot

    def start(self):
        self.start_for_notify()

    def check_max_notifies(self):
        if not self.event.sender.check_role(Role.TRUSTED) and \
                len(NotifyModel.objects.filter(user=self.event.user)) >= 5:
            raise PWarning("Нельзя добавлять более 5 напоминаний")

    def start_for_notify(self):
        self.check_max_notifies()
        timezone = self.event.sender.city.timezone.name

        arg0 = self.event.message.args[0]
        arg1 = self.event.message.args[1] if len(self.event.message.args) > 1 else None
        tz = self.event.sender.city.timezone

        date, args_count, exact_time_flag = self.get_time(arg0, arg1, tz)
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

        text = None
        split_text = self.event.message.args_str_case.split(' ', args_count)
        if len(split_text) > args_count:  # Если передан текст
            text = split_text[args_count]
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

        notify = NotifyModel(
            date=date,
            user=self.event.user,
            chat=self.event.chat,
            text_for_filter=notify_datetime.strftime("%d.%m.%Y %H:%M"),
            message_thread_id=self.event.message_thread_id
        )

        tg_att_flag = self.event.attachments and self.event.platform == Platform.TG
        if not (text or tg_att_flag):
            raise PWarning("В напоминании должны быть текст или вложения(tg)")
        if text:
            notify.text = text
            notify.text_for_filter += f" {text}"
        if tg_att_flag:
            notify.attachments = [{x.type: x.file_id} for x in self.event.attachments]

        notify.save()
        notify.text_for_filter += f" ({notify.id})"
        notify.save()

        return f'Сохранил на дату {str(notify_datetime.strftime("%d.%m.%Y %H:%M"))}'

    @staticmethod
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

        default_datetime = remove_tz(normalize_datetime(datetime.utcnow(), tz=timezone.name)).replace(hour=9, minute=0,
                                                                                                      second=0,
                                                                                                      microsecond=0)
        try:
            if arg1.count('.') == 1:
                arg1 = f"{arg1}.{default_datetime.year}"
            date_str = f"{arg1} {arg2}"

            return parser.parse(date_str, default=default_datetime, dayfirst=True), 2, exact_datetime_flag
        except ParserError:
            try:
                exact_datetime_flag = False
                return parser.parse(arg1, default=default_datetime, dayfirst=True), 1, exact_datetime_flag
            except ParserError:
                return None, None, None
