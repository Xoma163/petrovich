from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from apps.bot.core.messages.response_message import ResponseMessageItem
from apps.commands.gpt.commands.chatgpt import ChatGPTCommand
from apps.shared.exceptions import PWarning


class ChatHistoryTests(SimpleTestCase):
    def make_command(self, *args, reply_id=None):
        command = ChatGPTCommand()
        command.bot = Mock()
        command.event = SimpleNamespace(
            message=SimpleNamespace(id=100, args=[arg.lower() for arg in args], args_case=list(args)),
            fwd=[] if reply_id is None else [SimpleNamespace(message=SimpleNamespace(id=reply_id))],
            peer_id=123,
            message_thread_id=None,
            sender=Mock(),
            chat=Mock(),
            get_all_attachments=Mock(return_value=[Mock()]),
        )
        return command

    def test_defaults_and_count_formats(self):
        for args, expected_n, expected_prompt in (
            (("wtf",), 50, ChatGPTCommand.DEFAULT_PROMPT),
            (("wtf", "N=12"), 12, ChatGPTCommand.DEFAULT_PROMPT),
            (("wtf", "Опиши", "Решения", "15"), 15, "Опиши Решения"),
            (("wtf", "Опиши", "Решения", "N=15"), 15, "Опиши Решения"),
            (("wtf", "Опиши", "Решения"), 50, "Опиши Решения"),
        ):
            with self.subTest(args=args):
                command = self.make_command(*args)
                self.assertEqual(command._get_n_and_prompt(), (expected_n, expected_prompt))
                self.assertEqual(command.event.message.args_case, list(args))

    def test_invalid_count(self):
        for count in ("0", "-1", "N=0", "N=-2", "N=abc"):
            with self.subTest(count=count), self.assertRaises(PWarning):
                self.make_command("wtf", count)._get_n_and_prompt()

    def test_reply_selects_history_boundary(self):
        command = self.make_command("wtf", "Что", "Решили?", reply_id=75)
        self.assertEqual(command._get_n_and_prompt(), (25, "Что Решили?"))

    def test_explicit_wtf_routes_before_photos_and_reply_continuation(self):
        command = self.make_command("wtf", reply_id=75)
        command.set_provider_model = Mock()
        command.check_key = Mock(return_value=None)
        command.menu_chat_history = Mock(return_value=ResponseMessageItem(text="Саммари"))
        command._get_first_gpt_event_in_replies = Mock(return_value=Mock())

        command.start()

        command.check_key.assert_called_once_with()
        command.menu_chat_history.assert_called_once_with()
        command.event.get_all_attachments.assert_not_called()
        command._get_first_gpt_event_in_replies.assert_not_called()

    def test_wtf_still_requires_api_key(self):
        command = self.make_command("wtf")
        command.set_provider_model = Mock()
        command.check_key = Mock(side_effect=PWarning("Нет ключа"))
        command.menu_chat_history = Mock()

        with self.assertRaises(PWarning):
            command.start()

        command.menu_chat_history.assert_not_called()

    @patch("apps.commands.gpt.commands_utils.gpt.functionality.chat_history.ChatActionSender")
    def test_history_uses_current_gpt_instance_and_preprompt(self, chat_action_sender):
        command = self.make_command("wtf", "Что", "Решили?", "N=10")
        sender = SimpleNamespace(name="Анна")
        command.get_last_messages_as_events = Mock(return_value=[
            SimpleNamespace(is_from_user=True, sender=sender, message=SimpleNamespace(raw="Привет")),
            SimpleNamespace(is_from_user=True, sender=sender, message=SimpleNamespace(raw="Пойдём гулять")),
        ])
        command.get_preprompt = Mock(return_value=SimpleNamespace(text="Будь краток"))
        answer = ResponseMessageItem(text="Саммари")
        command.completions = Mock(return_value=answer)

        self.assertIs(command.menu_chat_history(), answer)

        command.get_last_messages_as_events.assert_called_once_with(10)
        command.get_preprompt.assert_called_once_with(command.event.sender, command.event.chat)
        history = command.completions.call_args.args[0]
        self.assertEqual([message.text for message in history.messages], [
            "Будь краток", "Что Решили?", "[Анна]\nПривет\nПойдём гулять",
        ])

    def test_voice_summary_callback_keeps_its_handler(self):
        command = self.make_command("_wtf")
        command.event.get_all_attachments.return_value = []
        command.set_provider_model = Mock()
        command.check_key = Mock(return_value=None)
        command._get_first_gpt_event_in_replies = Mock(return_value=None)
        command.menu_wtf = Mock(return_value=ResponseMessageItem(text="Голосовое"))
        command.menu_chat_history = Mock()

        command.start()

        command.menu_wtf.assert_called_once_with()
        command.menu_chat_history.assert_not_called()
