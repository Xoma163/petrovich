from unittest.mock import patch

from django.test import SimpleTestCase
from requests import HTTPError, Response

from apps.shared.utils.downloader import Downloader


class DownloaderTests(SimpleTestCase):
    @staticmethod
    def response(status, content):
        response = Response()
        response.status_code = status
        response._content = content
        return response

    def test_direct_download_accepts_successful_responses(self):
        for status in (200, 206):
            with self.subTest(status=status):
                with patch("apps.shared.utils.downloader.requests.get", return_value=self.response(status, b"video")):
                    self.assertEqual(Downloader().download_by_url("https://example.com/video"), b"video")

    def test_direct_download_rejects_http_errors(self):
        for status in (403, 404, 429, 500, 503):
            with self.subTest(status=status):
                with patch("apps.shared.utils.downloader.requests.get", return_value=self.response(status, b"Access Denied")):
                    with self.assertRaises(HTTPError):
                        Downloader().download_by_url("https://example.com/video")

    def test_chunk_download_rejects_http_errors(self):
        with patch("apps.shared.utils.downloader.requests.get", return_value=self.response(403, b"Access Denied")):
            with self.assertRaises(HTTPError):
                Downloader()._download_chunk("https://example.com/video", 0, 100)

    def test_parallel_download_rejects_head_error_before_fetching_chunks(self):
        with patch("apps.shared.utils.downloader.requests.head", return_value=self.response(403, b"")):
            with patch("apps.shared.utils.downloader.requests.get") as get:
                with self.assertRaises(HTTPError):
                    Downloader().download_in_parallel("https://example.com/video")
                get.assert_not_called()
