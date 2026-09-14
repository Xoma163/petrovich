import json
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from apps.connectors.parsers.media_command.boosty import Boosty
from apps.connectors.utils import get_default_headers


class BoostyTests(SimpleTestCase):
    @patch("apps.connectors.parsers.media_command.boosty.requests.get")
    def test_get_video_info_uses_downloader_user_agent_and_parses_duration(self, requests_get):
        initial_state = {
            "posts": {
                "postsList": {
                    "data": {
                        "posts": [
                            {
                                "data": [
                                    {
                                        "vid": "video-id",
                                        "duration": 125,
                                        "width": 1920,
                                        "height": 1080,
                                        "defaultPreview": "https://example.com/preview.jpg",
                                        "playerUrls": [
                                            {
                                                "type": "full_hd",
                                                "url": "https://example.com/video.mp4",
                                            },
                                        ],
                                    },
                                ],
                                "title": "Post title",
                                "user": {"id": "channel-id", "name": "Channel"},
                            },
                        ],
                    },
                },
            },
        }
        response = Mock()
        response.text = f'<script id="initial-state">{json.dumps(initial_state)}</script>'
        requests_get.return_value = response

        video_data = Boosty.get_video_info("https://boosty.to/channel/posts/post-id", "auth-cookie")

        requests_get.assert_called_once_with(
            "https://boosty.to/channel/posts/post-id",
            cookies={"auth": "auth-cookie"},
            headers=get_default_headers(),
            timeout=30,
        )
        response.raise_for_status.assert_called_once_with()
        self.assertEqual(video_data.duration, 125)
        self.assertEqual(video_data.extra_data["player_urls_dict"]["full_hd"], "https://example.com/video.mp4")
