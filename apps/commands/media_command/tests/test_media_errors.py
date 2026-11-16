from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase
from selenium.common import TimeoutException
from urllib3.exceptions import ReadTimeoutError

from apps.connectors.parsers.media_command.instagram import InstagramParser
from apps.connectors.parsers.media_command.tiktok import TikTok
from apps.commands.media_command.services.tiktok import TikTokService
from apps.connectors.parsers.media_command.vk_video import VKVideo
from apps.connectors.parsers.media_command.youtube.video import YoutubeVideo
from apps.shared.exceptions import PWarning
from apps.shared.utils.media_errors import media_request_errors


class MediaErrorTests(SimpleTestCase):
    def test_transport_errors_preserve_cause(self):
        cases = [
            (requests.Timeout(), "Медиасервис не ответил вовремя. Попробуйте позже"),
            (TimeoutException(), "Медиасервис не ответил вовремя. Попробуйте позже"),
            (ReadTimeoutError(None, "/session", "timeout"), "Медиасервис не ответил вовремя. Попробуйте позже"),
            (requests.exceptions.ChunkedEncodingError(), "Загрузка медиа оборвалась. Попробуйте ещё раз"),
            (requests.ConnectionError(), "Не удалось подключиться к медиасервису. Попробуйте позже"),
            (requests.RequestException(), "Не удалось загрузить медиа с сервиса. Попробуйте позже"),
        ]
        for error, message in cases:
            with self.subTest(error=type(error).__name__):
                with self.assertRaises(PWarning) as caught:
                    with media_request_errors():
                        raise error
                self.assertEqual(caught.exception.msg, message)
                self.assertIs(caught.exception.__cause__, error)

    def test_http_errors_do_not_claim_deletion_or_private_content(self):
        for status in (401, 403, 404, 429, 500):
            with self.subTest(status=status):
                response = requests.Response()
                response.status_code = status
                error = requests.HTTPError(response=response)
                with self.assertRaises(PWarning) as caught:
                    with media_request_errors():
                        raise error
                message = caught.exception.msg
                self.assertNotIn("удалено", message)
                self.assertNotIn("закрыт", message)
                self.assertIs(caught.exception.__cause__, error)
                if status == 429:
                    self.assertIn("ограничил число запросов", message)
                elif status in (401, 403):
                    self.assertIn("отказал в доступе", message)

    def test_existing_warnings_and_programming_errors_pass_through(self):
        for error in (PWarning("existing warning"), ValueError("parser error")):
            with self.subTest(error=type(error).__name__):
                with self.assertRaises(type(error)) as caught:
                    with media_request_errors():
                        raise error
                self.assertIs(caught.exception, error)

    def test_success_is_unchanged(self):
        with media_request_errors():
            result = 42
        self.assertEqual(result, 42)

    def test_ytdlp_messages(self):
        cases = [
            (YoutubeVideo, "Read timed out", "YouTube не отвечает при скачивании. Попробуйте позже"),
            (YoutubeVideo, "10 bytes read, 20 more expected", "Загрузка с YouTube оборвалась. Попробуйте ещё раз"),
            (YoutubeVideo, "Private video", "Это закрытое видео. Скачать без доступа нельзя"),
            (YoutubeVideo, "Sign in to confirm your age", "YouTube требует подтверждения возраста. Бот не может скачать это видео"),
            (YoutubeVideo, "Sign in to confirm you're not a bot", "YouTube заблокировал автоматическое скачивание. Попробуйте позже"),
            (YoutubeVideo, "Sign in to confirm you’re not a bot", "YouTube заблокировал автоматическое скачивание. Попробуйте позже"),
            (YoutubeVideo, "This video has been removed by the uploader", "Видео удалено с YouTube"),
            (YoutubeVideo, "Requested format is not available.", "Не удалось получить доступный формат видео. Попробуйте позже"),
            (YoutubeVideo, "unknown", "Не удалось скачать видео с YouTube. Попробуйте позже"),
            (VKVideo, "Read timed out", "VK Видео не отвечает при скачивании. Попробуйте позже"),
            (VKVideo, "10 bytes read, 20 more expected", "Загрузка с VK Видео оборвалась. Попробуйте ещё раз"),
            (VKVideo, "Private video", "Это закрытое видео. Скачать без доступа нельзя"),
            (VKVideo, "Video unavailable", "VK Видео сообщает, что видео недоступно"),
            (VKVideo, "unknown", "Не удалось скачать видео с VK Видео. Попробуйте позже"),
        ]
        for parser, error, message in cases:
            with self.subTest(parser=parser.__name__, error=error):
                result = parser._prepare_ytdlp_error(SimpleNamespace(msg=error))
                self.assertEqual(result.msg, message)
                self.assertNotIn("«", result.msg)
                self.assertNotIn("»", result.msg)

    def test_tiktok_timeout_does_not_claim_content_restriction(self):
        error = TimeoutException()
        with patch.object(TikTok, "_get_tiktok_request", side_effect=error):
            with self.assertRaises(PWarning) as caught:
                TikTok().get_video("https://www.tiktok.com/@user/video/1")
        self.assertEqual(caught.exception.msg, "Не удалось дождаться данных публикации TikTok. Попробуйте позже")
        self.assertIs(caught.exception.__cause__, error)

    def test_tiktok_rejects_non_video_download(self):
        for content in (b"", b"<HTML><HEAD><TITLE>Access Denied</TITLE></HEAD></HTML>", b"  <!doctype html><html></html>"):
            with self.subTest(content=content):
                service = TikTokService.__new__(TikTokService)
                service.service = Mock()
                service.service.get_video.return_value = SimpleNamespace(
                    video_download_url="https://example.com/video", thumbnail_url=None,
                    width=100, height=100, extra_data={"cookies": {}, "headers": {}},
                )
                service.event = SimpleNamespace(peer_id=1, message_thread_id=None)
                attachment = Mock(content=content)
                service.bot = Mock()
                service.bot.get_video_attachment.return_value = attachment
                with self.assertRaises(PWarning):
                    service._get_content_by_url("https://www.tiktok.com/@user/video/1")

    def test_tiktok_accepts_video_download(self):
        service = TikTokService.__new__(TikTokService)
        service.service = Mock()
        service.service.get_video.return_value = SimpleNamespace(
            video_download_url="https://example.com/video", thumbnail_url=None,
            width=100, height=100, extra_data={"cookies": {}, "headers": {}},
        )
        service.event = SimpleNamespace(peer_id=1, message_thread_id=None)
        attachment = Mock(content=b"\x00\x00\x00\x18ftypmp42")
        service.bot = Mock()
        service.bot.get_video_attachment.return_value = attachment
        self.assertEqual(service._get_content_by_url("https://www.tiktok.com/@user/video/1").attachments, [attachment])

    def test_instagram_empty_page_is_not_reported_as_deleted(self):
        with patch.object(InstagramParser, "_get_instagram_request", return_value=None):
            with self.assertRaises(PWarning) as caught:
                InstagramParser().get_data("https://www.instagram.com/p/test/")
        self.assertIn("Не удалось получить данные Instagram", caught.exception.msg)
