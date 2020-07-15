import datetime

from apps.bot.classes.Consts import Role
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

        if self.event.sender.city and self.event.sender.city.timezone:
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
            msg = "Такого пользователя нет"
        elif log is None:
            msg = "Информации пока ещё нет"
        else:
            localized_date = localize_datetime(remove_tz(log.date), timezone)
            msg = "%s\n%s" % (localized_date.strftime("%H:%M:%S"), log.msg)
        return str(msg)
