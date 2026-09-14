import json
from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase

from apps.commands.media_command.service import MediaKeys
from apps.commands.media_command.services.twitter import TwitterService
from apps.connectors.parsers.media_command.instagram import InstagramParser
from apps.connectors.parsers.media_command.twitter import TwitterAPIResponse
from apps.shared.exceptions import PWarning


class TwitterServiceTestCase(SimpleTestCase):
    def test_get_content_by_url_uses_existing_service_instance(self):
        event = SimpleNamespace(
            log_filter={"peer_id": 1},
            peer_id=1,
            message_thread_id=None,
        )
        bot = Mock()
        service = TwitterService(bot, event, media_keys=MediaKeys([], []), has_command_name=False)

        response = TwitterAPIResponse()
        response.caption = "caption"
        service.service = Mock()
        service.service.get_post_data.return_value = response

        result = service._get_content_by_url("https://x.com/test/status/1")

        service.service.get_post_data.assert_called_once_with("https://x.com/test/status/1")
        self.assertEqual(result.text, "caption")
        self.assertEqual(result.attachments, [])


class InstagramParserTestCase(SimpleTestCase):
    def test_get_media_finds_polaris_payload_at_any_require_position(self):
        media = {"video_versions": [{"url": "https://example.com/video.mp4"}]}
        page_data = {
            "require": [
                ["unrelated", None, None, [{"__bbox": {"result": {"data": {"other": {}}}}}]],
                [
                    "PolarisLoggedOutReelsPage",
                    None,
                    None,
                    [{"__bbox": {"result": {"data": {"xig_polaris_media": {"if_not_gated_logged_out": media}}}}}],
                ],
            ]
        }

        result = InstagramParser._get_media([SimpleNamespace(text=json.dumps(page_data))])

        self.assertEqual(result, media)

    def test_parse_media_keeps_caption_for_regular_media(self):
        data = InstagramParser._parse_media(
            {
                "caption": {"text": "caption"},
                "image_versions2": {"candidates": [{"url": "https://example.com/image.jpg"}]},
            }
        )

        self.assertEqual(data.caption, "caption")

    def test_parse_media_skips_caption_for_reels_media(self):
        data = InstagramParser._parse_media(
            {
                "caption": {"text": "caption"},
                "product_type": "clips",
                "video_versions": [{"url": "https://example.com/video.mp4"}],
            }
        )

        self.assertEqual(data.caption, "")

    def test_parse_media_can_skip_caption_by_url_type(self):
        data = InstagramParser._parse_media(
            {
                "caption": {"text": "caption"},
                "video_versions": [{"url": "https://example.com/video.mp4"}],
            },
            skip_caption=True,
        )

        self.assertEqual(data.caption, "")

    def test_get_polaris_media_rejects_api_age_gate(self):
        with self.assertRaisesMessage(PWarning, "возрастное ограничение"):
            InstagramParser._get_polaris_media(
                {
                    "__typename": "XIGPolarisVideoMedia",
                    "if_not_gated_logged_out": None,
                    "gating_ruling": {
                        "gating_type": 3,
                        "title": "Age-restricted content",
                    },
                }
            )

    def test_get_polaris_media_returns_ungated_payload(self):
        media = {"video_versions": [{"url": "https://example.com/video.mp4"}]}

        self.assertIs(
            InstagramParser._get_polaris_media({"if_not_gated_logged_out": media}),
            media,
        )
