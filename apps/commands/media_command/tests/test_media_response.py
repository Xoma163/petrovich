from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase

from apps.bot.core.bot.telegram.tg_bot import TgBot
from apps.commands.media_command.commands.media_command import Media
from apps.commands.media_command.services.reddit import RedditService
from apps.commands.media_command.services.youtube_video import YoutubeVideoService


class MediaResponseTestCase(SimpleTestCase):
    def test_source_response_disables_link_preview(self):
        for service in (YoutubeVideoService, RedditService):
            with self.subTest(service=service):
                command = Media()
                command.bot = Mock()
                command.bot.get_formatted_url = TgBot.get_formatted_url
                command.bot.send_response_message_item.return_value.success = True
                command._get_extra_text = Mock(return_value="")
                command.event = SimpleNamespace(
                    is_from_chat=False, fwd=[], peer_id=123, message_thread_id=456,
                    message=SimpleNamespace(id=789),
                )
                media_response = SimpleNamespace(
                    text="Описание", cache_url=None, need_to_wrap_html_tags=False, cache=None, attachments=[],
                )

                response = command.prepare_media_response(
                    media_response, SimpleNamespace(spoiler=False), "https://example.com/post", service,
                )

                rmi = response.messages[0]
                self.assertTrue(rmi.disable_web_page_preview)
                self.assertIn("Источник:", rmi.text)
                self.assertIn("https://example.com/post", rmi.text)
                self.assertEqual(rmi.has_rich_message, service == RedditService)
                command.bot.send_response_message_item.assert_called_once_with(rmi)
                command.bot.delete_messages.assert_called_once_with(123, 789)
