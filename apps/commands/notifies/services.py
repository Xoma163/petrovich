import datetime
import re
import zoneinfo
from dataclasses import dataclass
from typing import Any

from crontab import CronTab
from dateutil import parser
from dateutil.parser import ParserError
from django.db.models import Q, QuerySet

from apps.bot.consts import ATTACHMENT_TYPE_TRANSLATOR, PlatformEnum, RoleEnum
from apps.bot.core.event.event import Event
from apps.bot.core.messages.attachments.audio import AudioAttachment
from apps.bot.core.messages.attachments.document import DocumentAttachment
from apps.bot.core.messages.attachments.gif import AnimationAttachment
from apps.bot.core.messages.attachments.photo import PhotoAttachment
from apps.bot.core.messages.attachments.video import VideoAttachment
from apps.bot.core.messages.response_message import ResponseMessageItem
from apps.commands.notifies.models import Notify
from apps.shared.exceptions import PWarning
from apps.shared.utils.utils import localize_datetime, remove_tz

DELTA_WEEKDAY = {
    "сегодня": 0,
    "завтра": 1,
    "послезавтра": 2,
}

WEEK_TRANSLATOR = {
    "понедельник": 1,
    "пн": 1,
    "вторник": 2,
    "вт": 2,
    "среда": 3,
    "ср": 3,
    "четверг": 4,
    "чт": 4,
    "пятница": 5,
    "пт": 5,
    "суббота": 6,
    "сб": 6,
    "воскресенье": 7,
    "воскресение": 7,
    "вс": 7,
}

NOTIFY_ALLOWED_ATTACHMENTS = [
    AudioAttachment,
    DocumentAttachment,
    AnimationAttachment,
    PhotoAttachment,
    VideoAttachment,
]

REMINDER_MINIMUM_DELTA_SECONDS = 60


@dataclass(slots=True)
class ParsedReminderDate:
    date: datetime.datetime
    args_count: int
    allow_next_day_rollover: bool


@dataclass(slots=True)
class NotifyData:
    text: str
    date: datetime.datetime | None = None
    crontab: str | None = None
    attachments: list[dict[str, str]] | None = None
    user: Any | None = None
    chat: Any | None = None
    message_thread_id: int | None = None

    def as_model_kwargs(self) -> dict:
        return {
            "date": self.date,
            "crontab": self.crontab,
            "text": self.text,
            "attachments": self.attachments or [],
            "user": self.user,
            "chat": self.chat,
            "message_thread_id": self.message_thread_id,
        }


class ReminderDateParser:
    def __init__(self, dt_now: datetime.datetime, timezone_name: str):
        self.dt_now = dt_now
        self.timezone = zoneinfo.ZoneInfo(timezone_name)

    def parse(self, first_arg: str, second_arg: str | None) -> ParsedReminderDate | None:
        date_token, is_explicit_date = self._normalize_date_token(first_arg)
        default_datetime = self.current_local_datetime.replace(hour=9, minute=0, second=0, microsecond=0).replace(
            tzinfo=None
        )

        if second_arg is not None:
            parsed_datetime = self._parse_datetime_string(f"{date_token} {second_arg}", default_datetime)
            if parsed_datetime is not None:
                return ParsedReminderDate(
                    date=self._to_utc(parsed_datetime),
                    args_count=2,
                    allow_next_day_rollover=not is_explicit_date,
                )

        parsed_datetime = self._parse_datetime_string(date_token, default_datetime)
        if parsed_datetime is None:
            return None

        return ParsedReminderDate(
            date=self._to_utc(parsed_datetime),
            args_count=1,
            allow_next_day_rollover=self._is_time_only_input(first_arg),
        )

    def seconds_until(self, notify_datetime: datetime.datetime) -> float:
        return (notify_datetime - self.dt_now).total_seconds()

    def is_same_local_minute(self, notify_datetime: datetime.datetime) -> bool:
        local_notify_datetime = notify_datetime.astimezone(self.timezone)
        return local_notify_datetime.replace(second=0, microsecond=0) == self.current_local_datetime.replace(
            second=0,
            microsecond=0,
        )

    @property
    def current_local_datetime(self) -> datetime.datetime:
        return self.dt_now.astimezone(self.timezone)

    def _normalize_date_token(self, value: str) -> tuple[str, bool]:
        if value in DELTA_WEEKDAY:
            target_date = self.current_local_datetime.date() + datetime.timedelta(days=DELTA_WEEKDAY[value])
            return target_date.strftime("%d.%m.%Y"), False

        if value in WEEK_TRANSLATOR:
            delta_days = WEEK_TRANSLATOR[value] - self.current_local_datetime.isoweekday()
            if delta_days <= 0:
                delta_days += 7
            target_date = self.current_local_datetime.date() + datetime.timedelta(days=delta_days)
            return target_date.strftime("%d.%m.%Y"), False

        if value.count(".") == 1:
            return self._append_year_to_day_month(value), True

        return value, True

    def _append_year_to_day_month(self, value: str) -> str:
        try:
            parsed_date = datetime.datetime.strptime(value, "%d.%m").date()
        except ValueError as exc:
            raise PWarning("Ошибка парсинга даты") from exc

        year = self.current_local_datetime.year
        if (parsed_date.month, parsed_date.day) < (self.current_local_datetime.month, self.current_local_datetime.day):
            year += 1

        return f"{value}.{year}"

    @staticmethod
    def _parse_datetime_string(value: str, default_datetime: datetime.datetime) -> datetime.datetime | None:
        try:
            return parser.parse(value, default=default_datetime, dayfirst=True)
        except ParserError:
            return None
        except ValueError as exc:
            raise PWarning("Ошибка парсинга даты") from exc

    def _to_utc(self, value: datetime.datetime) -> datetime.datetime:
        return value.replace(tzinfo=self.timezone).astimezone(datetime.UTC)

    @staticmethod
    def _is_time_only_input(value: str) -> bool:
        return "." not in value and value not in DELTA_WEEKDAY and value not in WEEK_TRANSLATOR


class NotifyFormatter:
    def __init__(self, bot, timezone: str):
        self.bot = bot
        self.timezone = timezone

    def format_many(self, notifies: QuerySet[Notify] | list[Notify]) -> str:
        if not notifies:
            raise PWarning("Нет напоминаний")

        return "".join(self._format_one(notify) for notify in notifies).replace("@", "@_")

    def _format_one(self, notify: Notify) -> str:
        schedule = self._format_schedule(notify)
        notify_text = self._format_text(notify)
        chat_suffix = f" (Конфа - {notify.chat.name})" if notify.chat else ""
        return f"{notify.user}\n[id:{self.bot.get_formatted_text_line(notify.pk)}] {schedule}{chat_suffix}\n{notify_text}\n\n"

    def _format_schedule(self, notify: Notify) -> str:
        if notify.crontab:
            return self.bot.get_formatted_text_line(notify.crontab)

        notify_datetime = localize_datetime(remove_tz(notify.date), self.timezone)
        return self.bot.get_formatted_text_line(notify_datetime.strftime("%d.%m.%Y %H:%M"))

    def _format_text(self, notify: Notify) -> str:
        if notify.text and notify.attachments:
            return f"{self.bot.get_formatted_text_line(notify.text)} (вложения)"
        if notify.text:
            return self.bot.get_formatted_text_line(notify.text)
        return "(вложения)"


class NotifyQueryService:
    def __init__(self, event, bot):
        self.event = event
        self.bot = bot

    def get_filtered_notifies(self) -> QuerySet[Notify]:
        notifies = self._get_base_queryset()
        if not notifies.exists():
            raise PWarning("Нет активных напоминаний")
        return notifies.order_by("date", "pk")

    def get_notify(self, filters: list[str]) -> Notify:
        notifies = self.get_filtered_notifies()

        try:
            return notifies.get(pk=int(filters[0]))
        except ValueError, Notify.DoesNotExist:
            pass

        for item in filters:
            notifies = notifies.filter(Q(text__icontains=item) | Q(date__icontains=item) | Q(crontab__icontains=item))

        count = notifies.count()
        if count == 0:
            raise PWarning("Не нашёл напоминаний по такому тексту")
        if count > 1:
            formatter = NotifyFormatter(self.bot, self.event.sender.city.timezone.name)
            raise PWarning(f"Нашёл сразу {count}. Уточните:\n\n{formatter.format_many(notifies)}")

        return notifies.first()

    def _get_base_queryset(self) -> QuerySet[Notify]:
        if self.event.chat:
            return Notify.objects.filter(chat=self.event.chat)
        return Notify.objects.filter(user=self.event.user)


class NotifyCreateService:
    def __init__(self, event, full_names: list[str], dt_now: datetime.datetime | None = None):
        self.event = event
        self.full_names = full_names
        self.dt_now = dt_now or datetime.datetime.now(datetime.UTC)
        self.timezone_name = self.event.sender.city.timezone.name
        self.date_parser = ReminderDateParser(self.dt_now, self.timezone_name)

    def build_notify_data(self) -> NotifyData:
        notify_data = self._build_schedule_data()
        notify_data.attachments = self._serialize_attachments()
        notify_data.user = self.event.user
        notify_data.chat = self.event.chat
        notify_data.message_thread_id = self.event.message_thread_id

        self._validate_payload(notify_data)
        return notify_data

    def _build_schedule_data(self) -> NotifyData:
        try:
            crontab = self._get_crontab(self.event.message.args[1:])
            return self._build_repeat_notify_data(crontab)
        except ValueError:
            return self._build_single_notify_data()

    def _validate_payload(self, notify_data: NotifyData):
        if notify_data.text.startswith("/"):
            first_space = notify_data.text.find(" ")
            command = notify_data.text[1:first_space] if first_space > 0 else notify_data.text[1:]
            if command in self.full_names:
                raise PWarning("Нельзя добавлять напоминания с напоминаниями. АЛЛО, ТЫ ЧЁ МЕНЯ ХОЧЕШЬ СВАЛИТЬ?")

        has_tg_attachments = bool(notify_data.attachments) and self.event.platform == PlatformEnum.TG
        if not (notify_data.text or has_tg_attachments):
            raise PWarning("В напоминании должны быть текст или вложения(tg)")

    def _serialize_attachments(self) -> list[dict[str, str]]:
        return [
            {attachment.type: attachment.file_id}
            for attachment in self.event.get_all_attachments(NOTIFY_ALLOWED_ATTACHMENTS)
        ]

    def _build_single_notify_data(self) -> NotifyData:
        args_str_case = self.event.message.args_str_case.split(" ", 1)[1]
        first_arg = self.event.message.args[1]
        second_arg = self.event.message.args[2] if len(self.event.message.args) > 2 else None

        parsed_date = self.date_parser.parse(first_arg, second_arg)
        if parsed_date is None:
            raise PWarning("Не смог распарсить дату")

        scheduled_date = self._resolve_target_date(parsed_date)
        text = self._extract_text(args_str_case, parsed_date.args_count)
        return NotifyData(date=scheduled_date, text=text)

    def _resolve_target_date(self, parsed_date: ParsedReminderDate) -> datetime.datetime:
        initial_delta_seconds = self.date_parser.seconds_until(parsed_date.date)
        if 0 <= initial_delta_seconds <= REMINDER_MINIMUM_DELTA_SECONDS:
            raise PWarning("Нельзя добавлять напоминание на ближайшую минуту")

        if parsed_date.allow_next_day_rollover and self.date_parser.is_same_local_minute(parsed_date.date):
            raise PWarning("Нельзя добавлять напоминание на ближайшую минуту")

        target_date = parsed_date.date
        if parsed_date.allow_next_day_rollover and initial_delta_seconds < 0:
            target_date += datetime.timedelta(days=1)

        if self.date_parser.seconds_until(target_date) < 0:
            raise PWarning("Нельзя указывать дату в прошлом")

        return target_date

    @staticmethod
    def _extract_text(args_str_case: str, args_count: int) -> str:
        args_split = args_str_case.split(" ", args_count)
        if len(args_split) > args_count:
            return args_split[args_count]
        return ""

    def _build_repeat_notify_data(self, crontab: str) -> NotifyData:
        args_str_case = re.split(r"\s+", self.event.message.args_str_case, 1)[1]
        args_split = re.split(r"\s+", args_str_case, 5)
        return NotifyData(crontab=crontab, text=args_split[-1] if len(args_split) > 5 else "")

    @staticmethod
    def _get_crontab(crontab_args: list[str]) -> str:
        crontab_entry = " ".join(crontab_args[:5])
        CronTab(crontab_entry)
        return crontab_entry


class NotifyExecutionService:
    def __init__(self, dt_now: datetime.datetime | None = None):
        self.dt_now = dt_now or datetime.datetime.now(datetime.UTC)

    def should_send(self, notify: Notify) -> bool:
        if notify.user.profile.check_role(RoleEnum.BANNED):
            return False
        if notify.crontab:
            return self._is_crontab_due(notify)
        return self._is_one_time_notify_due(notify)

    def _is_crontab_due(self, notify: Notify) -> bool:
        timezone = notify.user.profile.city.timezone.name
        localized_datetime = localize_datetime(remove_tz(self.dt_now), timezone)
        entry = CronTab(notify.crontab)
        prev_seconds_delta = -entry.previous(localized_datetime, default_utc=True)
        return prev_seconds_delta <= 60

    def _is_one_time_notify_due(self, notify: Notify) -> bool:
        delta_time = remove_tz(notify.date) - remove_tz(self.dt_now) + datetime.timedelta(minutes=1)
        return delta_time.days == 0 and delta_time.seconds <= 60

    @staticmethod
    def build_response_message_item(bot, notify: Notify) -> ResponseMessageItem:
        answer = NotifyExecutionService._build_answer_text(bot, notify)
        attachments = NotifyExecutionService._build_attachments(notify)
        rmi = ResponseMessageItem(text=answer, attachments=attachments)

        if notify.chat:
            rmi.peer_id = notify.chat.chat_id
            rmi.message_thread_id = notify.message_thread_id
        else:
            rmi.peer_id = notify.user.user_id

        return rmi

    @staticmethod
    def _build_answer_text(bot, notify: Notify) -> str:
        if notify.date:
            notify_datetime = localize_datetime(remove_tz(notify.date), notify.user.profile.city.timezone.name)
            user_str = (
                f"{bot.get_mention(notify.user.profile)}:" if notify.mention_sender else f"{notify.user.profile}:"
            )
            return f"Напоминалка на {notify_datetime.strftime('%H:%M')}\n{user_str}\n{notify.text}"

        user_str = f"{bot.get_mention(notify.user.profile)}" if notify.mention_sender else f"{notify.user.profile}"
        return f"Напоминалка по {bot.get_formatted_text_line(notify.crontab)}\n{user_str}\n{notify.text}"

    @staticmethod
    def should_execute_command(notify: Notify) -> bool:
        return bool(notify.text and notify.text.startswith("/"))

    @staticmethod
    def build_command_event(notify: Notify) -> Event:
        event = Event()
        event.platform = PlatformEnum.TG
        event.set_message(notify.text)
        event.sender = notify.user.profile
        event.user = notify.user
        event.is_from_user = True
        event.message_thread_id = notify.message_thread_id
        event.is_notify = True

        if notify.chat:
            event.peer_id = notify.chat.chat_id
            event.chat = notify.chat
            event.is_from_chat = True
        else:
            event.peer_id = notify.user.user_id
            event.is_from_pm = True

        return event

    @staticmethod
    def _build_attachments(notify: Notify) -> list:
        attachments = []
        for attachment in notify.attachments or []:
            key = list(attachment.keys())[0]
            att = ATTACHMENT_TYPE_TRANSLATOR[key]()
            att.file_id = attachment[key]
            attachments.append(att)
        return attachments
