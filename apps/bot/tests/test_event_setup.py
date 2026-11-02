from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase

from apps.bot.core.bot.telegram.tg_bot import TgBot
from apps.bot.core.event.telegram.tg_event import TgEvent
from apps.bot.core.messages.attachments.audio import AudioAttachment
from apps.bot.core.messages.attachments.document import DocumentAttachment
from apps.bot.core.messages.attachments.photo import PhotoAttachment
from apps.commands.other.commands.moderator.logs import Logs


class TgEventDocumentTestCase(SimpleTestCase):
    @staticmethod
    def message():
        return {
            "message_id": 10,
            "from": {"id": 123, "is_bot": False, "first_name": "User"},
            "chat": {"id": -456, "type": "group"},
            "document": {"file_id": "file-id", "file_size": 100, "file_name": "script.py"},
            "caption": "Документ",
        }

    def test_document_without_mime_type_is_preserved(self):
        for mime_type in (None, "", "application/x-python", "image/png", "audio/mpeg"):
            with self.subTest(mime_type=mime_type):
                message = self.message()
                if mime_type is not None:
                    message["document"]["mime_type"] = mime_type
                event = TgEvent({"message": message}, use_db=False)

                event.setup_event()

                expected = {"image/png": PhotoAttachment, "audio/mpeg": AudioAttachment}.get(
                    mime_type, DocumentAttachment
                )
                self.assertIsInstance(event.attachments[0], expected)
                self.assertEqual(event.attachments[0].file_id, "file-id")
                self.assertEqual(event.message.raw, "Документ")
                if expected is DocumentAttachment:
                    if mime_type:
                        self.assertEqual(str(event.attachments[0].mime_type), mime_type)
                    else:
                        self.assertIsNone(event.attachments[0].mime_type.type)

    def test_reply_to_document_does_not_trigger_error_response(self):
        message = self.message()
        reply = {
            "message_id": 11,
            "from": message["from"],
            "chat": message["chat"],
            "text": "Обычный ответ",
            "reply_to_message": message,
        }
        event = TgEvent({"message": reply}, use_db=False)
        event.sender = Mock()
        event.sender.check_role.return_value = False
        event.need_a_response_extra = Mock(return_value=False)
        bot = TgBot()
        bot.route = Mock()
        bot.send_response_message = Mock()

        result = bot.handle_event(event)

        self.assertIsNone(result)
        bot.route.assert_not_called()
        bot.send_response_message.assert_not_called()
        self.assertIsInstance(event.fwd[0].attachments[0], DocumentAttachment)

    def test_audio_without_mime_type_is_preserved(self):
        audio = AudioAttachment()

        audio.parse_tg({"file_id": "audio-id", "file_size": 100, "file_name": "audio.mp3"})

        self.assertEqual(audio.file_id, "audio-id")


class EventSetupLoggingTestCase(SimpleTestCase):
    def test_setup_failure_has_context_visible_to_logs_command(self):
        event = TgEvent({"message": TgEventDocumentTestCase.message()}, use_db=False)
        setup_event = event.setup_event

        def fail_after_setup():
            setup_event()
            event.user = SimpleNamespace(user_id="123")
            event.chat = SimpleNamespace(chat_id="-456")
            raise RuntimeError("setup failure")

        event.setup_event = fail_after_setup
        bot = TgBot()
        bot.log_filter = {"user_id": "old", "chat_id": "old", "message_id": 999}
        bot.logger = Mock()
        bot.send_response_message = Mock()

        response = bot.handle_event(event, send=False)

        self.assertIn(bot.ERROR_MSG, response.messages[0].text)
        error = bot.logger.exception.call_args.args[0]
        self.assertEqual(error["log_filter"], {"user_id": "123", "chat_id": "-456", "message_id": 10})
        self.assertIsInstance(bot.logger.exception.call_args.kwargs["exc_info"], RuntimeError)
        command = Logs()
        command.event = event
        self.assertIsNotNone(command.filter_row({"levelname": "ERROR"}, error["log_filter"], ["ERROR"]))
