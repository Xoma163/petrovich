import traceback
from datetime import datetime, timedelta, date

from crontab import CronTab
from django.core.management.base import BaseCommand

from apps.bot.classes.Consts import Role
from apps.bot.classes.bots.CommonBot import get_bot_by_platform
from apps.bot.classes.events.Event import get_event_by_platform
from apps.service.models import Notify
from petrovich.settings import DEFAULT_TIME_ZONE


class Command(BaseCommand):

    def handle(self, *args, **options):
        from apps.bot.classes.common.CommonMethods import remove_tz, localize_datetime
        from apps.bot.classes.common.CommonMethods import get_attachments_for_upload

        notifies = Notify.objects.all()

        datetime_now = datetime.utcnow()
        for notify in notifies:
            try:
                if notify.author.check_role(Role.BANNED):
                    continue

                timezone_error = False
                if notify.repeat:
                    if notify.crontab:
                        try:
                            timezone = notify.author.city.timezone.name
                        except:
                            timezone_error = True
                            print("У пользователя слетела таймзона")
                            timezone = DEFAULT_TIME_ZONE
                        localized_datetime = localize_datetime(remove_tz(datetime_now), timezone)

                        entry = CronTab(notify.crontab)
                        prev_seconds_delta = - entry.previous(localized_datetime, default_utc=True)
                        flag = prev_seconds_delta <= 60
                    else:
                        datetime1 = datetime.combine(date.min, remove_tz(notify.date).time())
                        datetime2 = datetime.combine(date.min, datetime_now.time())
                        delta_time = datetime1 - datetime2 + timedelta(minutes=1)
                        flag = delta_time.seconds <= 60
                else:
                    delta_time = remove_tz(notify.date) - datetime_now + timedelta(minutes=1)
                    flag = delta_time.days == 0 and delta_time.seconds <= 60

                if flag:
                    attachments = []
                    if notify.chat:
                        platform = notify.chat.get_platform_enum()
                    else:
                        platform = notify.author.get_platform_enum()
                    bot = get_bot_by_platform(platform)()
                    event_model = get_event_by_platform(platform)

                    if notify.attachments and notify.attachments != "null":
                        notify_attachments = notify.attachments
                        attachments = get_attachments_for_upload(bot, notify_attachments)
                    if notify.date:
                        notify_datetime = localize_datetime(remove_tz(notify.date), notify.author.city.timezone.name)
                        message = f"Напоминалка на {notify_datetime.strftime('%H:%M')}\n" \
                                  f"{bot.get_mention(notify.author)}:\n" \
                                  f"{notify.text}"
                    else:
                        message = f"Напоминалка по {notify.crontab}\n" \
                                  f"{bot.get_mention(notify.author)}:\n" \
                                  f"{notify.text}"
                        if timezone_error:
                            message += "\n\nВАЖНО! Ваша таймзона слетела. " \
                                       "Проставьте город в профиле, чтобы напоминания по crontab приходили в корректное время"
                    result_msg = {'msg': message, 'attachments': attachments}
                    if notify.chat:
                        bot.parse_and_send_msgs_thread(notify.chat.chat_id, result_msg)
                    # Раскоментить если отправлять в лс пользователю, что это его напоминание
                    else:
                        # Если напоминание в ЛС и это не команда
                        # Если надо уведомлять о том, что будет выполнена команда - убираем условие
                        if not notify.text.startswith('/'):
                            bot.parse_and_send_msgs_thread(notify.author.user_id, result_msg)

                    # Если отложенная команда
                    if notify.text.startswith('/'):
                        # msg = notify.text[1:]
                        event = {
                            'message': {
                                'text': notify.text
                            },
                            'sender': notify.author,
                            'platform': platform
                        }
                        if notify.chat:
                            event['chat'] = notify.chat
                            event['peer_id'] = notify.chat.chat_id
                        else:
                            event['chat'] = None
                            event['peer_id'] = notify.author.user_id

                        event_object = event_model(event)
                        bot.menu(event_object, send=True)
                    if notify.repeat and not notify.crontab:
                        # Для постоянных уведомлений дата должа быть на завтрашний день обязательно.
                        # Это важно для сортировки
                        new_datetime = datetime.combine(datetime_now.date(), notify.date.time()) + timedelta(days=1)
                        new_datetime = localize_datetime(remove_tz(new_datetime), notify.author.city.timezone.name)
                        notify.date = new_datetime
                        notify.save()
                    else:
                        notify.delete()
            except Exception as e:
                print(str(e))
                tb = traceback.format_exc()
                print(tb)
