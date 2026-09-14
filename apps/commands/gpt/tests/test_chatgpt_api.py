import base64
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

    def test_dall_e_payload_also_omits_deprecated_response_format(self):
        model = SimpleNamespace(
            name="dall-e-3",
            size="1024x1024",
            quality="standard",
        )

        self.api.draw_image("draw a cat", model)

        payload = self.api.do_image_request.call_args.kwargs["json"]
        self.assertNotIn("response_format", payload)

    def test_fetch_image_request_decodes_base64_response(self):
        self.api.do_request = Mock(
            return_value={
                "data": [
                    {
                        "b64_json": base64.b64encode(b"image-bytes").decode(),
                        "revised_prompt": "a cat",
                    }
                ]
            }
        )

        image_bytes, prompt = self.api.fetch_image_request("https://api.openai.com/images/generations")

        self.assertEqual(image_bytes, b"image-bytes")
        self.assertEqual(prompt, "a cat")

    def test_fetch_image_request_downloads_url_response(self):
        self.api.do_request = Mock(
            return_value={
                "data": [
                    {
                        "url": "https://example.com/generated.png",
                        "revised_prompt": "a cat",
                    }
                ]
            }
        )
        image_response = Mock(content=b"image-bytes")
        self.api.requests.get = Mock(return_value=image_response)

        image_bytes, prompt = self.api.fetch_image_request("https://api.openai.com/images/generations")

        self.api.requests.get.assert_called_once_with("https://example.com/generated.png", log=False)
        image_response.raise_for_status.assert_called_once_with()
        self.assertEqual(image_bytes, b"image-bytes")
        self.assertEqual(prompt, "a cat")
