import traceback
from datetime import datetime, timedelta, date

from django.core.management.base import BaseCommand

from apps.bot.classes.bots.CommonBot import get_bot_by_platform
from apps.bot.classes.events.Event import get_event_by_platform
from apps.service.models import Notify


class Command(BaseCommand):

    def handle(self, *args, **options):
        from apps.bot.classes.common.CommonMethods import remove_tz, localize_datetime
        from apps.bot.classes.common.CommonMethods import get_attachments_for_upload

        notifies = Notify.objects.all()

        datetime_now = datetime.utcnow()
        for notify in notifies:
            try:
                if notify.repeat:
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
                        bot = get_bot_by_platform(notify.chat.platform)()
                        event_model = get_event_by_platform(notify.chat.platform)
                    else:
                        bot = get_bot_by_platform(notify.author.platform)()
                        event_model = get_event_by_platform(notify.author.platform)

                    if notify.attachments and notify.attachments != "null":
                        notify_attachments = notify.attachments
                        attachments = get_attachments_for_upload(bot, notify_attachments)

                    notify_datetime = localize_datetime(remove_tz(notify.date), notify.author.city.timezone.name)
                    message = f"Напоминалка на {notify_datetime.strftime('%H:%M')}\n" \
                              f"{bot.get_mention(notify.author)}:\n" \
                              f"{notify.text}"
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
                        msg = notify.text[1:]
                        event = {
                            'message': {
                                'text': msg
                            },
                            'sender': notify.author,
                            'platform': notify.author.platform
                        }
                        if notify.chat:
                            event['chat'] = notify.chat
                            event['peer_id'] = notify.chat.chat_id
                        else:
                            event['chat'] = None
                            event['peer_id'] = notify.author.user_id

                        event_object = event_model(event)
                        bot.menu(event_object, send=True)
                    if notify.repeat:
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
