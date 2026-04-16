import datetime
import logging

from django.core.management.base import BaseCommand

from apps.bot.core.bot.telegram.tg_bot import TgBot
from apps.commands.notifies.models import Notify
from apps.commands.notifies.services import NotifyExecutionService

logger = logging.getLogger("notifier")


class Command(BaseCommand):
    def __init__(self):
        super().__init__()
        self.executor = NotifyExecutionService(datetime.datetime.now(datetime.UTC))

    def handle(self, *args, **options):

        notifies = Notify.objects.select_related("chat", "user__profile__city__timezone").all()

        for notify in notifies:
            try:
                if not self.executor.should_send(notify):
                    continue

                bot = TgBot()
                rmi = self.executor.build_response_message_item(bot, notify)
                bot.send_response_message_item(rmi)
                logger.info(f"Отправил напоминание по id={notify.pk}")

                if self.executor.should_execute_command(notify):
                    event = self.executor.build_command_event(notify)
                    bot.handle_event(event)

                if notify.date:
                    notify.delete()
            except Exception:
                logger.exception("Ошибка в проверке/отправке оповещения")
