from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase

from apps.commands.media_command.service import MediaKeys
from apps.commands.media_command.services.twitter import TwitterService
from apps.connectors.parsers.media_command.twitter import TwitterAPIResponse


class TwitterServiceTestCase(SimpleTestCase):
    def test_get_content_by_url_uses_existing_service_instance(self):
        event = SimpleNamespace(
            log_filter={"peer_id": 1},
            peer_id=1,
            message_thread_id=None,
        )
        bot = Mock()
        service = TwitterService(
            bot, event, media_keys=MediaKeys([], []), has_command_name=False
        )

        response = TwitterAPIResponse()
        response.caption = "caption"
        service.service = Mock()
        service.service.get_post_data.return_value = response

        result = service._get_content_by_url("https://x.com/test/status/1")

        service.service.get_post_data.assert_called_once_with(
            "https://x.com/test/status/1"
        )
        self.assertEqual(result.text, "caption")
        self.assertEqual(result.attachments, [])
