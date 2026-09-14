from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase

from apps.commands.gpt.api.providers.chatgpt import ChatGPTAPI


class ChatGPTImageGenerationTests(SimpleTestCase):
    def setUp(self):
        self.api = ChatGPTAPI(api_key="test-key", log_filter={})
        self.api.do_image_request = Mock()

    def test_gpt_image_payload_omits_unsupported_response_format(self):
        model = SimpleNamespace(
            name="gpt-image-1",
            size="1024x1024",
            quality="medium",
        )

        self.api.draw_image("draw a cat", model)

        payload = self.api.do_image_request.call_args.kwargs["json"]
        self.assertNotIn("response_format", payload)
        self.assertEqual(payload["model"], "gpt-image-1")

    def test_dall_e_payload_requests_base64_response(self):
        model = SimpleNamespace(
            name="dall-e-3",
            size="1024x1024",
            quality="standard",
        )

        self.api.draw_image("draw a cat", model)

        payload = self.api.do_image_request.call_args.kwargs["json"]
        self.assertEqual(payload["response_format"], "b64_json")
