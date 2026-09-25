from unittest.mock import patch

from django.test import SimpleTestCase
from requests.exceptions import ChunkedEncodingError

from apps.bot.core.messages.attachments.attachment import Attachment


class AttachmentDownloadTests(SimpleTestCase):
    @patch("apps.shared.decorators.time.sleep")
    @patch(
        "apps.bot.core.messages.attachments.attachment.Downloader.download_by_url",
        side_effect=[ChunkedEncodingError("incomplete response"), b"complete response"],
    )
    def test_download_content_retries_incomplete_http_response(self, download_by_url, sleep):
        attachment = Attachment("document")
        attachment.public_download_url = "https://cdn.example/video.mp4"

        content = attachment.download_content()

        self.assertEqual(content, b"complete response")
        self.assertEqual(download_by_url.call_count, 2)
        sleep.assert_called_once_with(2)
