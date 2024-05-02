from datetime import datetime, timedelta

from crontab import CronTab
from dateutil import parser
from dateutil.parser import ParserError
from django.db.models import Q

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role, Platform
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.document import DocumentAttachment
from apps.bot.classes.messages.attachments.gif import GifAttachment
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import localize_datetime, normalize_datetime, remove_tz
from apps.service.models import Notify

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


class Notifies(Command):
    name = "напоминания"
    names = ["напоминание", "напомни", "напоминай"]

    help_text = HelpText(
        commands_text="список напоминаний",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand(None, "список активных напоминаний в лс, если в конфе, то только общие в конфе"),
                HelpTextItemCommand("добавить (дата/дата и время/день недели) (сообщение/команда) [вложения]",
                                    "добавляет напоминание"),
                HelpTextItemCommand("добавить (crontab) (сообщение/команда) [вложения]",
                                    "добавляет постоянное напоминание"),
                HelpTextItemCommand("удалить (текст/дата/crontab/id)", "удаляет напоминание")
            ])
        ],
        extra_text=(
            "Максимум можно добавить 5 напоминаний\n\nПомощник для добавления crontab: https://crontab.guru/"
        )
    )

    platforms = [Platform.TG]
    city = True

    bot: TgBot

    def start(self) -> ResponseMessage:
        arg0 = self.event.message.args[0] if self.event.message.args else None
        menu = [
            [["удалить", "удали"], self.menu_delete],
            [["добавить", "добавь"], self.menu_add],
            [['default'], self.menu_get_notifies],
        ]
        method = self.handle_menu(menu, arg0)
        rmi = method()
        return ResponseMessage(rmi)

    def menu_add(self) -> ResponseMessageItem:
        self.check_max_notifies()
        self.check_args(2)

        try:
            crontab = self._get_crontab(self.event.message.args[1:])
            data = self._add_notify_repeat(crontab)
        except ValueError:
            data = self._add_notify()

        attachments = self.event.get_all_attachments(
            [AudioAttachment, DocumentAttachment, GifAttachment, PhotoAttachment, VideoAttachment]
        )
        data.update({
            'attachments': [{x.type: x.file_id} for x in attachments] if attachments else [],
            'user': self.event.user,
            'chat': self.event.chat,
            'message_thread_id': self.event.message_thread_id
        })

        if data['text'] and data['text'][0] == '/':
            first_space = data['text'].find(' ')
            command = data['text'][1:first_space] if first_space > 0 else data['text'][1:]
            if command in self.full_names:
                raise PWarning("Нельзя добавлять напоминания с напоминаниями. АЛЛО, ТЫ ЧЁ МЕНЯ ХОЧЕШЬ СВАЛИТЬ?")

        tg_att_flag = attachments and self.event.platform == Platform.TG
        if not (data['text'] or tg_att_flag):
            raise PWarning("В напоминании должны быть текст или вложения(tg)")

        notify = Notify(**data)
        notify.save()

        if notify.crontab:
            answer = 'Добавил напоминание'
        else:
            timezone = self.event.sender.city.timezone.name
            localized_dt = localize_datetime(remove_tz(notify.date), timezone)
            answer = f'Сохранил на дату {localized_dt.strftime("%d.%m.%Y %H:%M")}'

        return ResponseMessageItem(text=answer)

    def menu_delete(self) -> ResponseMessageItem:
        self.check_args(2)

        channel_filter = self.event.message.args[1:]
        notifie = self.get_notifie(channel_filter)

        notifie.delete()
        answer = "Удалил"
        return ResponseMessageItem(text=answer)

    def menu_get_notifies(self) -> ResponseMessageItem:
        notifies = self.get_filtered_notifies()
        rmi = ResponseMessageItem(text=self.get_notifies_str(notifies, self.event.sender.city.timezone.name))
        return rmi

    def get_notifie(self, filters: list) -> Notify:
        notifies = self.get_filtered_notifies()

        try:
            pk = int(filters[0])
            notifies = notifies.get(pk=pk)
        except (ValueError, Notify.DoesNotExist):
            for _filter in filters:
                q = Q(text__icontains=_filter) | Q(date__icontains=_filter) | Q(crontab__icontains=_filter)
                notifies = notifies.filter(q)

        notifies_count = notifies.count()
        if notifies_count == 0:
            raise PWarning("Не нашёл напоминаний по такому тексту")
        elif notifies_count > 1:
            raise PWarning(f"Нашёл сразу {notifies_count}. Уточните:\n\n"
                           f"{self.get_notifies_str(notifies, self.event.sender.city.timezone.name)}")

        return notifies.first()

    def get_notifies_str(self, notifies_obj, timezone):
        if len(notifies_obj) == 0:
            raise PWarning("Нет напоминаний")
        result = ""

        for notify in notifies_obj:
            result += f"{notify.user}\n[id:{self.bot.get_formatted_text_line(notify.pk)}] "

            if notify.crontab:
                result += f"{self.bot.get_formatted_text_line(notify.crontab)}"
            else:
                notify_datetime = localize_datetime(remove_tz(notify.date), timezone)
                result += f"{self.bot.get_formatted_text_line(notify_datetime.strftime('%d.%m.%Y %H:%M'))}"
            if notify.chat:
                result += f" (Конфа - {notify.chat.name})"

            if notify.text and notify.attachments:
                notify_text = f"{self.bot.get_formatted_text_line(notify.text)} (вложения)"
            elif notify.text:
                notify_text = self.bot.get_formatted_text_line(notify.text)
            else:
                notify_text = "(вложения)"
            result += f"\n{notify_text}\n\n"

        result_without_mentions = result.replace('@', '@_')
        return result_without_mentions

    def get_filtered_notifies(self) -> Notify.objects:
        if self.event.chat:
            notifies = Notify.objects.filter(chat=self.event.chat)
        else:
            notifies = Notify.objects.filter(user=self.event.user)
        if notifies.count() == 0:
            raise PWarning("Нет активных напоминаний")
        return notifies.order_by("date")

    def check_max_notifies(self):
        if not self.event.sender.check_role(Role.TRUSTED) and \
                len(Notify.objects.filter(user=self.event.user)) >= 5:
            raise PWarning("Нельзя добавлять более 5 напоминаний")

    @staticmethod
    def _get_time(arg1, arg2, timezone=None):
        # Ад, угар и содомия. Вспомнить бы, как это работает
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

        default_datetime = remove_tz(normalize_datetime(datetime.utcnow(), tz=timezone.name)) \
            .replace(hour=9, minute=0, second=0, microsecond=0)
        try:
            if arg1.count('.') == 1:
                if datetime.strptime(f"{arg1}.{default_datetime.year}", '%d.%m.%Y') < datetime.utcnow():
                    arg1 = f"{arg1}.{default_datetime.year + 1}"
                else:
                    arg1 = f"{arg1}.{default_datetime.year}"
            date_str = f"{arg1} {arg2}"

            return parser.parse(date_str, default=default_datetime, dayfirst=True), 2, exact_datetime_flag
        except ParserError:
            try:
                exact_datetime_flag = False
                return parser.parse(arg1, default=default_datetime, dayfirst=True), 1, exact_datetime_flag
            except ParserError:
                return None, None, None

    def _add_notify(self) -> dict:
        timezone = self.event.sender.city.timezone.name
        # remove menu str
        args_str_case = self.event.message.args_str_case.split(' ', 1)[1]

        arg0 = self.event.message.args[1]
        arg1 = self.event.message.args[2] if len(self.event.message.args) > 2 else None
        tz = self.event.sender.city.timezone

        date, args_count, exact_time_flag = self._get_time(arg0, arg1, tz)
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
        args_split = args_str_case.split(' ', args_count)
        if len(args_split) > args_count:  # Если передан текст
            text = args_split[args_count]

        notify_dict = {
            'date': date,
            'text': text if text else ""
        }

        return notify_dict

    def _add_notify_repeat(self, crontab) -> dict:
        text = None
        # remove menu str
        args_str_case = self.event.message.args_str_case.split(' ', 1)[1]
        args_split = args_str_case.split(' ', 5)
        if len(args_split) > 5:
            text = args_split[-1]

        notify_dict = {
            'crontab': crontab,
            'text': text if text else ""
        }
        return notify_dict

    @staticmethod
    def _get_crontab(crontab_args):
        crontab_entry = " ".join(crontab_args[:5])
        CronTab(crontab_entry)
        return crontab_entry
