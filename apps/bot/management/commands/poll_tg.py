import logging
import time

from django.core.management.base import BaseCommand, CommandError

from apps.bot.core.bot.telegram.tg_bot import TgBot

logger = logging.getLogger("bot")


class Command(BaseCommand):
    help = "Запускает Telegram long polling для локального дебага без webhook."

    def add_arguments(self, parser):
        parser.add_argument("--timeout", type=int, default=30, help="Таймаут getUpdates в секундах.")
        parser.add_argument("--limit", type=int, default=20, help="Максимум апдейтов за один запрос.")
        parser.add_argument("--sleep", type=float, default=1, help="Пауза после ошибок polling в секундах.")
        parser.add_argument("--once", action="store_true", help="Обработать одну пачку апдейтов и выйти.")
        parser.add_argument(
            "--drop-webhook",
            action="store_true",
            help="Снять webhook перед polling. Нужно, если Telegram возвращает конфликт getUpdates/webhook.",
        )
        parser.add_argument(
            "--drop-pending-updates",
            action="store_true",
            help="При снятии webhook удалить накопленные апдейты.",
        )

    def handle(self, *args, **options):
        bot = TgBot()
        offset = None

        if options["drop_webhook"]:
            response = bot.api_handler.delete_webhook(drop_pending_updates=options["drop_pending_updates"])
            if not response.get("ok"):
                raise CommandError(response)
            self.stdout.write(self.style.SUCCESS("Telegram webhook снят"))

        self.stdout.write("Telegram polling запущен")
        while True:
            try:
                response = bot.api_handler.get_updates(
                    offset=offset,
                    limit=options["limit"],
                    timeout=options["timeout"],
                )
                if not response.get("ok"):
                    raise CommandError(response)

                updates = response.get("result", [])
                for update in updates:
                    offset = update["update_id"] + 1
                    bot.parse(update)

                if options["once"]:
                    return
            except KeyboardInterrupt:
                self.stdout.write("Telegram polling остановлен")
                return
            except CommandError:
                raise
            except Exception:
                logger.exception("Ошибка Telegram polling")
                if options["once"]:
                    raise
                time.sleep(options["sleep"])
