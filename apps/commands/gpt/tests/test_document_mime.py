from unittest.mock import Mock

from django.test import SimpleTestCase

from apps.bot.core.messages.attachments.document import DocumentAttachment, DocumentMimeType
from apps.commands.gpt.commands.chatgpt import ChatGPTCommand
from apps.commands.gpt.messages.consts import GPTMessageRole
from apps.commands.gpt.messages.openai_responses import OpenAIResponsesMessage


class DocumentMimeTestCase(SimpleTestCase):
    def test_unknown_mime_properties_are_false(self):
        for value in (None, ""):
            with self.subTest(value=value):
                mime_type = DocumentMimeType(value)

                self.assertFalse(mime_type.is_image)
                self.assertFalse(mime_type.is_audio)
                self.assertFalse(mime_type.is_text)
                self.assertFalse(mime_type.is_pdf)
                self.assertEqual(str(mime_type), "")

    def test_text_extension_fallback_without_mime(self):
        for extension in ("txt", "html", "bin"):
            with self.subTest(extension=extension):
                document = DocumentAttachment()
                document.ext = extension
                document.read_text = Mock(return_value="Содержимое")
                event = Mock()
                event.get_all_attachments.return_value = [document]

                text = ChatGPTCommand()._get_common_msg_text(event, "Вопрос")

                if extension in ("txt", "html"):
                    self.assertIn("Содержимое", text)
                    document.read_text.assert_called_once()
                else:
                    self.assertEqual(text, "Вопрос")
                    document.read_text.assert_not_called()

    def test_only_known_pdf_is_added_to_history(self):
        unknown = DocumentAttachment()
        pdf = DocumentAttachment()
        pdf.mime_type = DocumentMimeType("application/pdf")
        event = Mock()
        event.get_all_attachments.side_effect = [[], [unknown, pdf]]
        history = Mock()

        ChatGPTCommand()._add_common_message(history, event, GPTMessageRole.USER, "Вопрос")

        history.add_message.assert_called_once_with(GPTMessageRole.USER, "Вопрос", [], [pdf])

    def test_serializer_skips_unknown_mime(self):
        document = DocumentAttachment()
        document.base64 = Mock()
        message = OpenAIResponsesMessage(GPTMessageRole.USER, "Вопрос", files=[document])

        result = message.get_message()

        self.assertEqual(result["content"], [{"type": "input_text", "text": "Вопрос"}])
        document.base64.assert_not_called()

    def test_wtf_without_mime_keeps_extension_fallback(self):
        for extension in ("txt", "bin"):
            with self.subTest(extension=extension):
                document = DocumentAttachment()
                document.ext = extension
                document.read_text = Mock(return_value="Содержимое")
                command = ChatGPTCommand()
                command.event = Mock()
                command.event.raw = {"callback_query": {"message": {"caption": "Подпись"}}}
                command.event.get_all_attachments.return_value = [document]
                command.get_preprompt = Mock(return_value=None)
                command.completions = Mock()
                command.send_rmi = Mock()

                command.menu_wtf()

                history = command.completions.call_args.args[0]
                self.assertEqual(history.messages[-1].text, "Содержимое" if extension == "txt" else "Подпись")
