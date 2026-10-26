import logging

import requests

from apps.bot.core.messages.attachments.audio import AudioAttachment
from apps.connectors.api.handler import API
from apps.shared.exceptions import PError
from petrovich.settings import env


logger = logging.getLogger(__name__)


class WhisperAPI(API):
    def transcribe(self, audio: AudioAttachment) -> str:
        base_url = env.str("WHISPER_API_BASE_URL", default="http://127.0.0.1:11033/v1").rstrip("/")
        api_key = env.str("WHISPER_API_KEY", default="")
        if not api_key:
            raise PError("Не настроен ключ сервиса распознавания речи")
        content = audio.download_content()
        try:
            with self.requests.post(
                f"{base_url}/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files={"file": (f"voice.{audio.ext}", content, "application/octet-stream")},
                data={
                    "model": env.str("WHISPER_API_MODEL", default="mobiuslabsgmbh/faster-whisper-large-v3-turbo"),
                    "language": "ru",
                    "response_format": "json",
                },
                timeout=(5, env.int("WHISPER_API_TIMEOUT", default=600)),
                log=False,
            ) as response:
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict) or not isinstance(payload.get("text"), str):
                    raise ValueError("Invalid Whisper API response")
                return payload["text"].strip()
        except (requests.RequestException, ValueError) as e:
            logger.exception("Whisper API recognition failed", extra=self.log_filter)
            raise PError("Не получилось распознать голосовое сообщение через сервис Whisper") from e
