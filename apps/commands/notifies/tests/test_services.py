import datetime
from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.bot.consts import PlatformEnum
from apps.bot.core.messages.message import Message
from apps.shared.exceptions import PWarning
from apps.commands.notifies.services import NotifyExecutionService
from apps.commands.notifies.services import NotifyCreateService


class NotifyExecutionServiceTestCase(SimpleTestCase):
    def test_should_execute_command(self):
        notify = SimpleNamespace(text="/помощь")

        self.assertTrue(NotifyExecutionService.should_execute_command(notify))

    def test_should_not_execute_plain_text(self):
        notify = SimpleNamespace(text="просто текст")

        self.assertFalse(NotifyExecutionService.should_execute_command(notify))

    def test_build_command_event_for_chat(self):
        profile = SimpleNamespace()
        user = SimpleNamespace(profile=profile, user_id=123)
        chat = SimpleNamespace(chat_id=456)
        notify = SimpleNamespace(text="/помощь", user=user, chat=chat, message_thread_id=789)

        event = NotifyExecutionService.build_command_event(notify)

        self.assertEqual(event.peer_id, 456)
        self.assertEqual(event.chat, chat)
        self.assertEqual(event.user, user)
        self.assertEqual(event.sender, profile)
        self.assertEqual(event.message_thread_id, 789)
        self.assertTrue(event.is_from_chat)
        self.assertFalse(event.is_from_pm)
        self.assertTrue(event.is_notify)
        self.assertEqual(event.message.command, "помощь")

    def test_build_command_event_for_pm(self):
        profile = SimpleNamespace()
        user = SimpleNamespace(profile=profile, user_id=123)
        notify = SimpleNamespace(text="/помощь", user=user, chat=None, message_thread_id=None)

        event = NotifyExecutionService.build_command_event(notify)

        self.assertEqual(event.peer_id, 123)
        self.assertIsNone(event.chat)
        self.assertTrue(event.is_from_pm)
        self.assertFalse(event.is_from_chat)
        self.assertTrue(event.is_notify)


class NotifyCreateServiceTestCase(SimpleTestCase):
    def setUp(self):
        self.dt_now = datetime.datetime(2026, 4, 16, 12, 34, tzinfo=datetime.UTC)
        self.timezone = SimpleNamespace(name="UTC")
        self.city = SimpleNamespace(timezone=self.timezone)
        self.sender = SimpleNamespace(city=self.city)

    def test_past_time_creates_notify_for_next_day(self):
        service = self._create_service("напоминания добавить 12:33 тест")

        notify_data = service._build_single_notify_data()

        self.assertEqual(notify_data.date, datetime.datetime(2026, 4, 17, 12, 33, tzinfo=datetime.UTC))

    def test_current_time_raises_warning(self):
        service = self._create_service("напоминания добавить 12:34 тест")

        with self.assertRaisesMessage(PWarning, "Нельзя добавлять напоминание на ближайшую минуту"):
            service._build_single_notify_data()

    def test_next_minute_raises_warning(self):
        service = self._create_service("напоминания добавить 12:35 тест")

        with self.assertRaisesMessage(PWarning, "Нельзя добавлять напоминание на ближайшую минуту"):
            service._build_single_notify_data()

    def test_today_past_time_moves_to_next_day(self):
        service = self._create_service("напоминания добавить сегодня 12:33 тест")

        notify_data = service._build_single_notify_data()

        self.assertEqual(notify_data.date, datetime.datetime(2026, 4, 17, 12, 33, tzinfo=datetime.UTC))

    def test_day_month_in_past_moves_to_next_year(self):
        service = self._create_service("напоминания добавить 15.04 12:36 тест")

        notify_data = service._build_single_notify_data()

        self.assertEqual(notify_data.date, datetime.datetime(2027, 4, 15, 12, 36, tzinfo=datetime.UTC))

    def test_weekday_resolves_to_next_occurrence(self):
        service = self._create_service("напоминания добавить понедельник 12:36 тест")

        notify_data = service._build_single_notify_data()

        self.assertEqual(notify_data.date, datetime.datetime(2026, 4, 20, 12, 36, tzinfo=datetime.UTC))

    def test_same_minute_time_only_raises_warning_instead_of_next_day(self):
        service = self._create_service(
            "напоминания добавить 10:47 тест",
            dt_now=datetime.datetime(2026, 4, 16, 10, 47, 32, tzinfo=datetime.UTC),
        )

        with self.assertRaisesMessage(PWarning, "Нельзя добавлять напоминание на ближайшую минуту"):
            service._build_single_notify_data()

    def test_previous_minute_time_only_still_rolls_to_next_day(self):
        service = self._create_service(
            "напоминания добавить 10:46 тест",
            dt_now=datetime.datetime(2026, 4, 16, 10, 47, 32, tzinfo=datetime.UTC),
        )

        notify_data = service._build_single_notify_data()

        self.assertEqual(notify_data.date, datetime.datetime(2026, 4, 17, 10, 46, tzinfo=datetime.UTC))

    def _create_service(self, raw_message: str, dt_now: datetime.datetime | None = None) -> NotifyCreateService:
        message = Message(raw_message)
        event = SimpleNamespace(
            sender=self.sender,
            message=message,
            user=SimpleNamespace(),
            chat=None,
            message_thread_id=None,
            platform=PlatformEnum.TG,
            get_all_attachments=lambda *_args, **_kwargs: [],
        )
        return NotifyCreateService(event, [], dt_now=dt_now or self.dt_now)
