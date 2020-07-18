import json
from datetime import datetime, timedelta

from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import localize_datetime, normalize_datetime, remove_tz, check_user_group
from apps.service.models import Notify as NotifyModel


def get_time(time):
    try:
        date = datetime.strptime(str(datetime.today().date()) + " " + time, "%Y-%m-%d %H:%M")
        return date
    except ValueError:
        return None


class NotifyRepeat(CommonCommand):
    def __init__(self):
        names = ["напоминай", "оповещай"]
        help_text = "Напоминай - напоминает о чём-либо постояно"
        detail_help_text = "Напоминай (время) (сообщение/команда) [Прикреплённые вложения] - напоминает о чём-то каждый день в заданное время\n" \
                           "Максимум можно добавить 5 напоминаний"
        super().__init__(names, help_text, detail_help_text, args=2, platforms=['vk', 'tg'], city=True)

    def start(self):
        if not check_user_group(self.event.sender, Role.TRUSTED) and \
                len(NotifyModel.objects.filter(author=self.event.sender)) >= 5:
            return "Нельзя добавлять более 5 напоминаний"
        timezone = self.event.sender.city.timezone.name

        date = get_time(self.event.args[0])
        if not date:
            return "Не смог распарсить дату"
        date = normalize_datetime(date, timezone)
        datetime_now = localize_datetime(datetime.utcnow(), "UTC")

        if (date - datetime_now).seconds < 60:
            return "Нельзя добавлять напоминание на ближайшую минуту"

        if (date - datetime_now).days < 0 or (datetime_now - date).seconds < 0:
            date = date + timedelta(days=1)

        text = self.event.original_args.split(' ', 1)[1]
        if text[0] == '/':
            first_space = text.find(' ')
            if first_space > 0:
                command = text[1:first_space]
            else:
                command = text[1:]
            from apps.bot.commands.Notify import Notify
            if command in self.names or command in Notify().names:
                text = f"/обосрать {self.event.sender.name}"
        notify_datetime = localize_datetime(remove_tz(date), timezone)

        notify = NotifyModel(date=date,
                             text=text,
                             author=self.event.sender,
                             chat=self.event.chat,
                             repeat=True,
                             text_for_filter=notify_datetime.strftime("%H:%M") + " " + text,
                             attachments=json.dumps(self.event.attachments))

        notify.save()
        notify.text_for_filter += f" ({notify.id})"
        notify.save()

        return f'Следующее выполнение - {str(notify_datetime.strftime("%d.%m.%Y %H:%M"))}'
