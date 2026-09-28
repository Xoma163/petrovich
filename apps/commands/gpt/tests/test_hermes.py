import base64
from io import BytesIO
from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase
from PIL import Image

from apps.commands.gpt.api.providers.hermes import HermesAPI
from apps.commands.gpt.commands.hermes import HermesCommand
from apps.commands.gpt.messages.consts import GPTMessageRole
from apps.commands.gpt.messages.openai_completions import OpenAICompletionsMessage
from apps.shared.exceptions import PWarning


class HermesAPITest(SimpleTestCase):
    def setUp(self):
        self.api = HermesAPI(api_key="test-secret", log_filter={})
        self.model = Mock(name="hermes-agent")
        self.model.name = "hermes-agent"
        self.messages = OpenAICompletionsMessage()
        self.messages.add_message(GPTMessageRole.USER, "Привет")

    @patch("apps.commands.gpt.api.providers.hermes.env.str", return_value="http://localhost:8642/v1/")
    @patch("apps.commands.gpt.api.providers.hermes.requests.post")
    def test_completions(self, post, env_str):
        response = post.return_value
        response.json.return_value = {
            "choices": [{"message": {"content": "Здравствуйте"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 3},
        }

        result = self.api.completions(self.messages, self.model, {})

        self.assertEqual(result.text, "Здравствуйте")
        self.assertEqual(result.usage.input_tokens, 12)
        self.assertEqual(result.usage.output_tokens, 3)
        post.assert_called_once_with(
            "http://localhost:8642/v1/chat/completions",
            json={
                "model": "hermes-agent",
                "messages": [
                    {"role": "system", "content": HermesAPI.IMAGE_INSTRUCTION},
                    *self.messages.get_messages(),
                ],
                "stream": False,
            },
            headers={"Authorization": "Bearer test-secret"},
            timeout=(5, 300),
        )

    @patch("apps.commands.gpt.api.providers.hermes.env.str", return_value="http://localhost:8642/v1")
    @patch("apps.commands.gpt.api.providers.hermes.requests.post")
    def test_failure_is_not_exposed_to_user(self, post, env_str):
        post.side_effect = requests.ConnectionError("secret URL")

        with self.assertRaises(PWarning) as error:
            self.api.completions(self.messages, self.model, {})

        self.assertNotIn("secret URL", str(error.exception))

    @patch("apps.commands.gpt.api.providers.hermes.env.str", return_value="http://localhost:8642/v1")
    @patch("apps.commands.gpt.api.providers.hermes.requests.post")
    def test_agent_failure_does_not_return_partial_answer(self, post, env_str):
        post.return_value.json.return_value = {
            "choices": [{"message": {"content": "Partial"}, "finish_reason": "error"}],
        }

        with self.assertRaises(PWarning):
            self.api.completions(self.messages, self.model, {})

    @patch("apps.commands.gpt.api.providers.hermes.env.str", return_value="")
    @patch("apps.commands.gpt.api.providers.hermes.requests.post")
    def test_missing_configuration_does_not_send_request(self, post, env_str):
        with self.assertRaises(PWarning):
            self.api.completions(self.messages, self.model, {})
        post.assert_not_called()

    def test_command_is_admin_only(self):
        self.assertEqual(HermesCommand.access.name, "ADMIN")


class HermesImageTest(SimpleTestCase):
    def setUp(self):
        self.command = HermesCommand()
        self.command.event = Mock()
        self.command.event.message.id = 42
        self.command.event.peer_id = 123
        self.command.event.message_thread_id = None
        self.command.bot = Mock(max_rich_message_text_length=32768)
        image = BytesIO()
        Image.new("RGB", (2, 2), "yellow").save(image, format="PNG")
        self.encoded = base64.b64encode(image.getvalue()).decode("ascii")

    def test_inline_image_becomes_telegram_photo_with_caption(self):
        rmi = self.command.get_completions_rmi(f"Вот жираф.\n![image](data:image/png;base64,{self.encoded})")

        self.assertEqual(rmi.text, "Вот жираф.")
        self.assertEqual(len(rmi.attachments), 1)
        self.assertEqual(rmi.attachments[0].type, "photo")
        self.assertEqual(rmi.reply_to, 42)
        self.assertEqual(rmi.peer_id, 123)
        self.assertNotIn(self.encoded, rmi.text)

    def test_image_without_caption_is_sent(self):
        rmi = self.command.get_completions_rmi(f"![image](data:image/png;base64,{self.encoded})")

        self.assertEqual(rmi.text, "")
        self.assertEqual(len(rmi.attachments), 1)

    def test_multiple_images_are_preserved(self):
        inline = f"![image](data:image/png;base64,{self.encoded})"
        rmi = self.command.get_completions_rmi(f"{inline}\n{inline}")

        self.assertEqual(len(rmi.attachments), 2)
        self.assertNotEqual(rmi.attachments[0].file_name_full, rmi.attachments[1].file_name_full)

    def test_invalid_image_does_not_leak_base64(self):
        rmi = self.command.get_completions_rmi("![image](data:image/png;base64,ZmFrZQ==)")

        self.assertEqual(rmi.attachments, [])
        self.assertNotIn("ZmFrZQ==", rmi.text)

    def test_plain_text_uses_existing_behavior(self):
        rmi = self.command.get_completions_rmi("Привет")

        self.assertEqual(rmi.text, "Привет")
        self.assertEqual(rmi.attachments, [])
