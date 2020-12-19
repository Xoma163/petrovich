import datetime

from apps.bot.classes.Consts import Role
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import localize_datetime, remove_tz
from apps.db_logger.models import MovementLog
from petrovich.settings import TIME_ZONE


class Where(CommonCommand):
    def __init__(self):
        names = ["где"]
        help_text = "Где - информация о чекточках"
        detail_help_text = "Где (N) - информация о чекточках, где N - имя, фамилия, логин/id, никнейм"
        super().__init__(names, help_text, detail_help_text, args=1, access=Role.TRUSTED)

    def start(self):

        user = self.bot.get_user_by_name(self.event.args, self.event.chat)

        if self.event.sender.city:
            timezone = self.event.sender.city.timezone.name
        else:
            timezone = TIME_ZONE
        today = localize_datetime(datetime.datetime.utcnow(), timezone)
        log = MovementLog.objects.filter(success=True,
                                         date__year=today.year,
                                         date__month=today.month,
                                         date__day=today.day,
                                         author=user).first()
        if user is None:
            raise PWarning("Такого пользователя нет")
        if log is None:
            raise PWarning("Информации пока ещё нет")
        localized_date = localize_datetime(remove_tz(log.date), timezone).strftime("%H:%M:%S")
        return f"{localized_date}\n{log.msg}"
