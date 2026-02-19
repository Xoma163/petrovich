from apps.bot.consts import RoleEnum
from apps.bot.core.event.event import Event
from apps.bot.core.messages.response_message import ResponseMessage
from apps.commands.command import Command
from apps.shared.exceptions import PSkipContinue, PWarning


class CheckTrustedRole(Command):
    names = None
    # Обоснование: команда должна запускаться перед всеми остальными командами, но после экшенов
    priority = 99

    def accept(self, event: Event) -> bool:
        return True

    def start(self) -> ResponseMessage | None:
        if self.event.sender and not self.event.sender.check_role(RoleEnum.TRUSTED):
            raise PWarning("Обратитесь за доступом к создателю бота.")
        raise PSkipContinue()
