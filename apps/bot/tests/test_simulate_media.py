import json
from io import StringIO
from unittest.mock import patch

import requests
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TransactionTestCase, override_settings

from apps.bot.consts import RoleEnum
from apps.bot.core.messages.attachments.video import VideoAttachment
from apps.bot.core.messages.response_message import ResponseMessage
from apps.bot.management.commands.simulate_media import SimulatedBot
from apps.bot.models import Role
from apps.commands.media_command.service import MediaServiceResponse
from apps.shared.exceptions import PWarning


class SimulateMediaTests(TransactionTestCase):
    def setUp(self):
        for role in (RoleEnum.USER, RoleEnum.TRUSTED):
            Role.objects.create(name=role.name)

    def test_rejects_non_media_before_creating_user(self):
        with self.assertRaises(CommandError):
            call_command("simulate_media", "/удалить всё", stdout=StringIO())

    @override_settings(DATABASES={"default": {"HOST": "production.example", "PORT": "5432"}})
    def test_rejects_non_local_database(self):
        with self.assertRaises(CommandError):
            call_command("simulate_media", "https://vt.tiktok.com/ZSpvKVcts/", stdout=StringIO())

    @patch("apps.commands.media_command.services.tiktok.TikTokService.get_content_by_url")
    def test_reports_downloaded_bytes_without_telegram(self, get_content):
        attachment = VideoAttachment()
        attachment.content = b"video"
        get_content.return_value = MediaServiceResponse(text=None, attachments=[attachment], video_title="")
        output = StringIO()

        with patch("apps.bot.core.bot.telegram.tg_bot.TelegramAPI") as telegram_api:
            call_command("simulate_media", "https://vt.tiktok.com/ZSpvKVcts/", stdout=output)

        telegram_api.return_value.send_video.assert_not_called()
        result = json.loads(output.getvalue())
        self.assertEqual(result["messages"][0]["attachments"], [{"type": "video", "bytes": 5, "source_host": None}])
        self.assertEqual(result["errors"], [])

    @patch("apps.commands.media_command.services.tiktok.TikTokService.get_content_by_url")
    def test_calls_handle_event_without_telegram(self, get_content):
        get_content.side_effect = PWarning("Медиасервис отказал в доступе. Не удалось загрузить медиа")
        output = StringIO()

        with patch("apps.bot.core.bot.telegram.tg_bot.TelegramAPI") as telegram_api:
            call_command("simulate_media", "https://vt.tiktok.com/ZSpvKVcts/", stdout=output)

        telegram_api.assert_called_once()
        telegram_api.return_value.send_message.assert_not_called()
        result = json.loads(output.getvalue())
        self.assertEqual(
            result["messages"][0]["text"], "Медиасервис отказал в доступе. Не удалось загрузить медиа", result
        )
        self.assertEqual(result["errors"][0]["type"], "PWarning")

    def test_sanitizes_http_error_url(self):
        bot = SimulatedBot()
        response = requests.Response()
        response.status_code = 403
        response.url = "https://v16-webapp-prime.tiktok.com/video?signature=private"
        error = requests.HTTPError(response=response)
        warning = PWarning("403")
        warning.__cause__ = error
        bot.log_message(ResponseMessage(), exc_info=warning)

        self.assertEqual(bot.errors, [{"type": "HTTPError", "status": 403, "host": "v16-webapp-prime.tiktok.com"}])
