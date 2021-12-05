import traceback
from datetime import datetime, timedelta, date

from crontab import CronTab
from django.core.management.base import BaseCommand

from apps.bot.classes.bots.Bot import get_bot_by_platform
from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.classes.events.Event import Event
from apps.bot.utils.utils import remove_tz, localize_datetime, get_tg_formatted_text_line
from apps.service.models import Notify


class Command(BaseCommand):

    def __init__(self):
        super().__init__()
        self.dt_now = datetime.utcnow()

    def handle(self, *args, **options):

        notifies = Notify.objects.all()

        for notify in notifies:
            try:
                if notify.text == 'https://www.youtube.com/watch?v=V_cnK8Cd6Ag' and notify.user.profile.name == "Андрей":
                    flag = True
                else:
                    flag = self.get_flag_by_notify(notify)
                if not flag:
                    continue

                platform = notify.chat.get_platform_enum() if notify.chat else notify.user.get_platform_enum()
                bot = get_bot_by_platform(platform)

                self.send_notify_message(bot, notify)
                self.send_command_notify_message(bot, notify)
                if notify.repeat:
                    self.extend_repeat_notify(notify)
                else:
                    notify.delete()
            except Exception as e:
                print(str(e))
                tb = traceback.format_exc()
                print(tb)

    def get_flag_by_notify(self, notify):

        if notify.user.profile.check_role(Role.BANNED):
            return False

        if notify.repeat:
            if notify.crontab:
                timezone = notify.user.profile.city.timezone.name
                localized_datetime = localize_datetime(remove_tz(self.dt_now), timezone)

                entry = CronTab(notify.crontab)
                prev_seconds_delta = - entry.previous(localized_datetime, default_utc=True)
                return prev_seconds_delta <= 60
            else:
                datetime1 = datetime.combine(date.min, remove_tz(notify.date).time())
                datetime2 = datetime.combine(date.min, self.dt_now.time())
                delta_time = datetime1 - datetime2 + timedelta(minutes=1)
                return delta_time.seconds <= 60
        else:
            delta_time = remove_tz(notify.date) - self.dt_now + timedelta(minutes=1)
            return delta_time.days == 0 and delta_time.seconds <= 60

    @staticmethod
    def send_notify_message(bot, notify):
        if notify.date:
            notify_datetime = localize_datetime(remove_tz(notify.date), notify.user.profile.city.timezone.name)
            message = f"Напоминалка на {notify_datetime.strftime('%H:%M')}\n" \
                      f"{bot.get_mention(notify.user.profile)}:\n" \
                      f"{notify.text}"
        else:
            if notify.user.get_platform_enum() == Platform.TG:
                message = f"Напоминалка по {get_tg_formatted_text_line(notify.crontab)}\n"
            else:
                message = f"Напоминалка по {notify.crontab}\n"
            message += f" {bot.get_mention(notify.user.profile)} \n" \
                       f"{notify.text}"

        result_msg = {'text': message}

        if notify.chat:
            bot.parse_and_send_msgs(result_msg, notify.chat.chat_id)
        else:
            if not notify.text.startswith('/'):
                bot.parse_and_send_msgs(result_msg, notify.user.user_id)

    @staticmethod
    def send_command_notify_message(bot, notify):
        # Если отложенная команда

        if notify.text.startswith('/'):
            event = Event(bot=bot)
            event.set_message(notify.text)
            event.sender = notify.user.profile
            event.is_from_user = True
            if notify.chat:
                event.peer_id = notify.chat.chat_id
                event.chat = notify.chat
                event.is_from_chat = True
            else:
                event.peer_id = notify.user.user_id
                event.is_from_pm = True

            bot.handle_event(event)

    def extend_repeat_notify(self, notify):
        if notify.date:
            # Для постоянных уведомлений дата должа быть на завтрашний день обязательно.
            # Это важно для сортировки
            new_datetime = datetime.combine(self.dt_now.date(), notify.date.time()) + timedelta(days=1)
            new_datetime = localize_datetime(remove_tz(new_datetime), notify.user.profile.city.timezone.name)
            notify.date = new_datetime
            notify.save()
