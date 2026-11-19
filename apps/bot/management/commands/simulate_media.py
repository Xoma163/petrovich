import json
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.bot.consts import PlatformEnum, RoleEnum
from apps.bot.core.bot.bot import Bot
from apps.bot.core.bot.telegram.tg_bot import TgBot
from apps.bot.core.bot_response import BotResponse
from apps.bot.core.event.telegram.tg_event import TgEvent
from apps.bot.models import Role
from apps.commands.media_command.commands.media_command import Media
from apps.shared.utils.utils import get_urls_from_text


class OfflineTelegramAPI:
    def __getattr__(self, name):
        raise RuntimeError(f"Telegram API is disabled in simulate_media: {name}")


class SimulatedBot(TgBot):
    def __init__(self):
        Bot.__init__(self, PlatformEnum.TG)
        self.api_handler = OfflineTelegramAPI()
        self.sent = []
        self.errors = []

    def set_chat_action(self, chat_id, chat_action, message_thread_id=None):
        pass

    def send_response_message_item(self, rmi):
        self.sent.append(rmi)
        return BotResponse(True, {"ok": True})

    def delete_messages(self, chat_id, message_ids):
        return {"ok": True}

    def log_event(self, event):
        pass

    def log_message(self, message, level="debug", exc_info=None):
        if exc_info is not None:
            cause = exc_info.__cause__ or exc_info
            response = getattr(cause, "response", None)
            status = getattr(response, "status_code", None)
            url = getattr(response, "url", None)
            self.errors.append(
                {
                    "type": type(cause).__name__,
                    "status": status,
                    "host": urlparse(url).hostname if url else None,
                }
            )


class Command(BaseCommand):
    help = "Run a local media message through handle_event without contacting Telegram."

    def add_arguments(self, parser):
        parser.add_argument("text", help="Message containing one supported media URL")
        parser.add_argument("--user-id", type=int, default=900000000001)

    def handle(self, *args, **options):
        db = settings.DATABASES["default"]
        redis = settings.CACHES["default"].get("LOCATION", "")
        if db.get("HOST") not in ("localhost", "127.0.0.1") or str(db.get("PORT")) != "15433":
            raise CommandError("Only the local Docker PostgreSQL on 127.0.0.1:15433 is allowed")
        if not str(redis).startswith("redis://127.0.0.1:16380/"):
            raise CommandError("Only the local Docker Redis on 127.0.0.1:16380 is allowed")

        text = options["text"]
        urls = get_urls_from_text(text)
        if len(urls) != 1 or urlparse(urls[0]).hostname not in Media.all_urls():
            raise CommandError("Provide exactly one supported media URL; other commands are not allowed")
        if text.strip() != urls[0] and text.strip() != f"/медиа {urls[0]}":
            raise CommandError("Only a URL or '/медиа URL' is allowed")
        if options["user_id"] <= 0:
            raise CommandError("user-id must be positive")

        role = Role.objects.get(name=RoleEnum.TRUSTED.name)
        bot = SimulatedBot()
        user_id = options["user_id"]
        raw = {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "from": {"id": user_id, "is_bot": False, "first_name": "Local media test"},
                "chat": {"id": user_id, "type": "private"},
                "text": text,
            },
        }
        event = TgEvent(raw)
        event.bot = bot
        # A synthetic user exists only in the local Docker database.
        from apps.bot.utils import get_profile_by_user_id

        profile = get_profile_by_user_id(user_id, PlatformEnum.TG)
        profile.roles.add(role)
        response = bot.handle_event(event)
        messages = bot.sent or (response.messages if response else [])
        result = {
            "messages": [
                {
                    "text": item.text,
                    "attachments": [
                        {
                            "type": attachment.type,
                            "bytes": len(attachment.content or b""),
                            "source_host": urlparse(attachment.public_download_url).hostname
                            if attachment.public_download_url
                            else None,
                        }
                        for attachment in item.attachments
                    ],
                }
                for item in messages
            ],
            "errors": bot.errors,
        }
        self.stdout.write(json.dumps(result, ensure_ascii=False))
