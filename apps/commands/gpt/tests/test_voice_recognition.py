from types import SimpleNamespace
from unittest.mock import Mock, patch

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

    @patch("apps.commands.gpt.commands.voice_recognition.ChatActionSender")
    @patch("apps.commands.gpt.commands.voice_recognition.WhisperAPI")
    def test_start_delegates_to_whisper_then_restores_punctuation(self, api, chat_action_sender):
        command = self._get_command()
        audio = Mock(ext="ogg")
        command.event.peer_id = 123
        command.event.message_thread_id = None
        command.event.log_filter = {"peer_id": 123}
        command.event.get_all_attachments = Mock(return_value=[audio])
        api.return_value.transcribe.return_value = "привет"
        command.restore_punctuation_qwen = Mock(return_value="Привет.")
        command._get_rmi = Mock(return_value=command._get_rmi("Привет."))

        command.start()

        chat_action_sender.assert_called_once()
        command.event.get_all_attachments.assert_called_once_with(command.attachments)
        audio.get_file.assert_called_once_with()
        api.assert_called_once_with(log_filter=command.event.log_filter)
        api.return_value.transcribe.assert_called_once_with(audio)
        command.restore_punctuation_qwen.assert_called_once_with("привет")
        command._get_rmi.assert_called_once_with("Привет.")

    def test_long_transcription_uses_rich_text_instead_of_document(self):
        command = self._get_command()
        answer = "а" * 5000

        result = command._get_rmi(answer)

        self.assertEqual(result.text, answer)
        self.assertEqual(result.rich_markdown, f"> {answer}\n>||")
        self.assertEqual(result.attachments, [])
        self.assertEqual(result.reply_to, 123)
        self.assertEqual(result.keyboard, {"keyboard": "summary"})

    @patch("apps.commands.gpt.commands.voice_recognition.Usage")
    @patch("apps.commands.gpt.commands.voice_recognition.QwenAPI")
    @patch("apps.commands.gpt.commands.voice_recognition.CompletionsModel.objects.get")
    @patch("apps.commands.gpt.commands.voice_recognition.Provider.objects.get")
    def test_punctuation_uses_qwen_api_without_chat_provider(self, get_provider, get_model, api, usage):
        command = self._get_command()
        command.event.log_filter = {"peer_id": 123}
        command.event.sender = Mock()
        response = api.return_value.completions.return_value
        response.text = "Привет."

        self.assertEqual(command.restore_punctuation_qwen("привет"), "Привет.")

        get_provider.assert_called_once_with(name="qwen")
        get_model.assert_called_once_with(provider=get_provider.return_value, is_default=True)
        api.assert_called_once_with(log_filter=command.event.log_filter, api_key="")
        messages = api.return_value.completions.call_args.args[0].get_messages()
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("привет", messages[1]["content"][0]["text"])
        usage.return_value.save.assert_called_once_with()

    @patch("apps.commands.gpt.commands.voice_recognition.QwenAPI")
    @patch("apps.commands.gpt.commands.voice_recognition.CompletionsModel.objects.get")
    @patch("apps.commands.gpt.commands.voice_recognition.Provider.objects.get")
    def test_punctuation_keeps_whisper_text_when_qwen_fails(self, get_provider, get_model, api):
        command = self._get_command()
        command.event.log_filter = {"peer_id": 123}
        api.return_value.completions.side_effect = RuntimeError("Qwen unavailable")

        with self.assertLogs("apps.commands.gpt.commands.voice_recognition", level="WARNING"):
            self.assertEqual(command.restore_punctuation_qwen("привет"), "привет")

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
