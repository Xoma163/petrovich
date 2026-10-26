from unittest.mock import Mock, patch, MagicMock

import requests

from django.test import SimpleTestCase

from apps.connectors.api.whisper import WhisperAPI
from apps.shared.exceptions import PError


class WhisperAPITests(SimpleTestCase):
    def setUp(self):
        self.api = WhisperAPI(log_filter={})
        self.audio = Mock(ext="ogg")
        self.audio.download_content.return_value = b"audio"
        self.env_patch = patch("apps.connectors.api.whisper.env")
        env = self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        self.logger_patch = patch("apps.connectors.api.whisper.logger.exception")
        self.logger_patch.start()
        self.addCleanup(self.logger_patch.stop)
        self.values = {
            "WHISPER_API_BASE_URL": "http://localhost:11033/v1/",
            "WHISPER_API_KEY": "test-key",
        }
        env.str.side_effect = lambda name, default=None: self.values.get(name, default)
        env.int.return_value = 600

    @patch("apps.connectors.api.handler.requests.post")
    def test_posts_audio_and_parses_text(self, post):
        response = MagicMock()
        post.return_value.__enter__.return_value = response
        response.json.return_value = {"text": "  Привет  "}
        self.assertEqual(self.api.transcribe(self.audio), "Привет")
        self.assertEqual(post.call_args.args[0], "http://localhost:11033/v1/audio/transcriptions")
        self.assertEqual(post.call_args.kwargs["headers"], {"Authorization": "Bearer test-key"})
        self.assertEqual(post.call_args.kwargs["files"]["file"][1], b"audio")
        self.assertEqual(post.call_args.kwargs["timeout"], (5, 600))
        self.assertEqual(
            post.call_args.kwargs["data"]["model"], "mobiuslabsgmbh/faster-whisper-large-v3-turbo"
        )

    @patch("apps.connectors.api.handler.requests.post")
    def test_model_is_configurable(self, post):
        self.values["WHISPER_API_MODEL"] = "custom/model"
        post.return_value.__enter__.return_value.json.return_value = {"text": "Привет"}
        self.api.transcribe(self.audio)
        self.assertEqual(post.call_args.kwargs["data"]["model"], "custom/model")

    @patch("apps.connectors.api.handler.requests.post")
    def test_missing_key_does_not_send_audio(self, post):
        self.values["WHISPER_API_KEY"] = ""
        with self.assertRaises(PError):
            self.api.transcribe(self.audio)
        post.assert_not_called()
        self.audio.download_content.assert_not_called()

    @patch("apps.connectors.api.handler.requests.post")
    def test_timeout_becomes_user_error(self, post):
        post.side_effect = requests.Timeout("timeout")
        with self.assertRaises(PError):
            self.api.transcribe(self.audio)

    @patch("apps.connectors.api.handler.requests.post")
    def test_invalid_response_becomes_user_error(self, post):
        response = MagicMock()
        post.return_value.__enter__.return_value = response
        for payload in ({}, {"text": None}, []):
            with self.subTest(payload=payload):
                response.json.return_value = payload
                with self.assertRaises(PError):
                    self.api.transcribe(self.audio)

    @patch("apps.connectors.api.handler.requests.post")
    def test_http_error_becomes_user_error(self, post):
        post.return_value.__enter__.return_value.raise_for_status.side_effect = requests.HTTPError("429")
        with self.assertRaises(PError):
            self.api.transcribe(self.audio)
