import logging
from datetime import datetime, timedelta, date

from crontab import CronTab
from django.core.management.base import BaseCommand

from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.consts.Consts import Role, ATTACHMENT_TYPE_TRANSLATOR
from apps.bot.classes.events.Event import Event
from apps.bot.classes.messages.ResponseMessage import ResponseMessageItem
from apps.bot.utils.utils import remove_tz, localize_datetime
from apps.service.models import Notify

logger = logging.getLogger('notifier')


class Command(BaseCommand):

    def __init__(self):
        super().__init__()
        self.dt_now = datetime.utcnow()

    def handle(self, *args, **options):

        notifies = Notify.objects.all()

        for notify in notifies:
            try:
                flag = self.get_flag_by_notify(notify)
                if not flag:
                    continue
                bot = TgBot()

                self.send_notify_message(bot, notify)
                self.send_command_notify_message(bot, notify)
                if notify.repeat:
                    self.extend_repeat_notify(notify)
                else:
                    notify.delete()
            except Exception:
                logger.exception("Ошибка в проверке/отправке оповещения")

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
            user_str = f"{bot.get_mention(notify.user.profile)}:" if notify.mention_sender else f"{notify.user.profile}:"
            answer = f"Напоминалка на {notify_datetime.strftime('%H:%M')}\n" \
                     f"{user_str}\n" \
                     f"{notify.text}"
        else:
            answer = f"Напоминалка по {bot.get_formatted_text_line(notify.crontab)}\n"
            user_str = f"{bot.get_mention(notify.user.profile)}" if notify.mention_sender else f"{notify.user.profile}"
            answer += f"{user_str}\n" \
                      f"{notify.text}"

        attachments = []
        if notify.attachments:
            for attachment in notify.attachments:
                key = list(attachment.keys())[0]
                value = attachment[key]
                att = ATTACHMENT_TYPE_TRANSLATOR[key]()
                att.file_id = value
                attachments.append(att)
        rmi = ResponseMessageItem(text=answer, attachments=[attachments])
        logger.info(f"Отправил напоминание по id={notify.pk}")

        if notify.chat:
            rmi.peer_id = notify.chat.chat_id
            rmi.message_thread_id = notify.message_thread_id
        else:
            if not notify.text.startswith('/'):
                rmi.peer_id = notify.user.user_id
        bot.send_response_message_item(rmi)

    @staticmethod
    def send_command_notify_message(bot, notify):
        # Если отложенная команда

        if notify.text.startswith('/'):
            event = Event(bot=bot)
            event.set_message(notify.text)
            event.sender = notify.user.profile
            event.is_from_user = True
            event.message_thread_id = notify.message_thread_id
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
