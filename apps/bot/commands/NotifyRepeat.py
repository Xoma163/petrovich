from datetime import datetime, timedelta

from crontab import CronTab

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.utils import localize_datetime, normalize_datetime, remove_tz
from apps.service.models import Notify as NotifyModel


def get_time(time):
    try:
        date = datetime.strptime(str(datetime.today().date()) + " " + time, "%Y-%m-%d %H:%M")
        return date
    except ValueError:
        return None


def get_crontab(crontab_args):
    crontab_entry = " ".join(crontab_args[:5])
    CronTab(crontab_entry)
    return crontab_entry


class NotifyRepeat(Command):
    name = "напоминай"
    help_text = "напоминает о чём-либо постояно"
    help_texts = [
        "(время) (сообщение/команда) - напоминает о чём-то каждый день в заданное время. Максимум можно добавить 5 напоминаний",
        "(crontab) (сообщение/команда) - напоминает о чём-то с помощью crontab. Максимум можно добавить 5 напоминаний"
    ]
    args = 2
    platforms = [Platform.VK, Platform.TG]
    city = True

    def start(self):
        if not self.event.sender.check_role(Role.TRUSTED) and \
                len(NotifyModel.objects.filter(user=self.event.sender)) >= 5:
            raise PWarning("Нельзя добавлять более 5 напоминаний")
        timezone = self.event.sender.city.timezone.name

        crontab = None
        date = None
        try:
            crontab = get_crontab(self.event.message.args_case)
            args_split = self.event.message.args_str_case.split(' ', 5)
            if len(args_split) > 5:
                text = args_split[-1]
            else:
                text = ""
        except Exception:
            date = get_time(self.event.message.args[0])
            if not date:
                raise PWarning("Не смог распарсить дату")
            date = normalize_datetime(date, timezone)
            datetime_now = localize_datetime(datetime.utcnow(), "UTC")

            if (date - datetime_now).seconds < 60:
                raise PWarning("Нельзя добавлять напоминание на ближайшую минуту")

            if (date - datetime_now).days < 0 or (datetime_now - date).seconds < 0:
                date = date + timedelta(days=1)

            text = self.event.message.args_str_case.split(' ', 1)[1]
        if text and text[0] == '/':
            first_space = text.find(' ')
            if first_space > 0:
                command = text[1:first_space]
            else:
                command = text[1:]
            from apps.bot.commands.Notify import Notify
            if command in self.full_names or command in Notify().full_names:
                text = f"/обосрать {self.event.sender.name}"
        if date:
            notify_datetime = localize_datetime(remove_tz(date), timezone)

        if crontab:
            notify = NotifyModel(
                crontab=crontab,
                text=text,
                user=self.event.user,
                chat=self.event.chat,
                repeat=True,
                text_for_filter=f'{crontab} {text}'
            )
        else:
            notify = NotifyModel(
                date=date,
                text=text,
                user=self.event.user,
                chat=self.event.chat,
                repeat=True,
                text_for_filter=f'{notify_datetime.strftime("%H:%M")} {text}'
            )
        notify.save()
        notify.text_for_filter += f" ({notify.id})"
        notify.save()
        if date:
            return f'Следующее выполнение - {str(notify_datetime.strftime("%d.%m.%Y %H:%M"))}'
        else:
            return 'Добавил напоминание'
