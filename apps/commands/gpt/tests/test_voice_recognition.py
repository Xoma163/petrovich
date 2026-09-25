from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase

from apps.commands.gpt.commands.voice_recognition import VoiceRecognition


class VoiceRecognitionResponseTests(SimpleTestCase):
    @staticmethod
    def _get_command() -> VoiceRecognition:
        command = VoiceRecognition.__new__(VoiceRecognition)
        command.bot = Mock()
        command.bot.max_message_text_length = 4096
        command.bot.max_rich_message_text_length = 32768
        command.bot.get_quote_text.side_effect = lambda text, expandable: f"<blockquote>{text}</blockquote>"
        command.bot.get_expandable_quote_markdown.side_effect = lambda text: f"> {text}\n>||"
        command.bot.get_button.return_value = {"button": "summary"}
        command.bot.get_inline_keyboard.return_value = {"keyboard": "summary"}
        command.event = SimpleNamespace(message=SimpleNamespace(id=123))
        return command

    def test_long_transcription_uses_rich_text_instead_of_document(self):
        command = self._get_command()
        answer = "а" * 5000

        result = command._get_rmi(answer)

        self.assertEqual(result.text, answer)
        self.assertEqual(result.rich_markdown, f"> {answer}\n>||")
        self.assertEqual(result.attachments, [])
        self.assertEqual(result.reply_to, 123)
        self.assertEqual(result.keyboard, {"keyboard": "summary"})

    def test_short_transcription_keeps_regular_expandable_quote(self):
        command = self._get_command()
        answer = "а" * 500

        result = command._get_rmi(answer)

        self.assertEqual(result.text, f"<blockquote>{answer}</blockquote>")
        self.assertIsNone(result.rich_markdown)
        self.assertEqual(result.attachments, [])

    def test_very_long_transcription_still_uses_document(self):
        command = self._get_command()
        answer = "а" * 33000

        result = command._get_rmi(answer)

        self.assertEqual(result.text, "Полная транскрибация в одном файле")
        self.assertIsNone(result.rich_markdown)
        self.assertEqual(len(result.attachments), 1)
        self.assertEqual(result.attachments[0].file_name, "Транскрибация")
        self.assertEqual(result.attachments[0].ext, "html")
