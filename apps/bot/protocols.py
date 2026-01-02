from typing import Protocol, Callable

from apps.bot.classes.bots.bot import Bot
from apps.bot.classes.const.consts import Role
from apps.bot.classes.event.event import Event
from apps.bot.classes.help_text import HelpText
from apps.bot.classes.messages.response_message import ResponseMessage


class CommandProtocol(Protocol):
    name: str
    names: list

    help_text: HelpText | None

    enabled: bool
    suggest_for_similar: bool
    priority: int
    hidden: bool

    abstract: bool

    # Проверки
    access: Role
    pm: bool
    conversation: bool
    fwd: bool
    args: int
    args_or_fwd: bool
    int_args: list
    float_args: list
    platforms: list
    excluded_platforms: list
    attachments: list
    city: bool
    mentioned: bool
    non_mentioned: bool

    def __init__(self, bot: Bot = None, event: Event = None): ...  # noqa

    bot: Bot
    event: Event

    def accept(self, event: Event) -> bool: ...

    def check_and_start(self, bot: Bot, event: Event) -> ResponseMessage: ...

    def checks(self) -> None: ...

    def start(self) -> ResponseMessage | None: ...

    def check_sender(self, role: Role) -> None: ...

    def check_args(self, args: int = None) -> bool: ...

    def check_args_or_fwd(self, args: int = None) -> bool: ...

    @staticmethod
    def check_number_arg_range(arg, _min=-float('inf'), _max=float('inf'), banned_list: list = None) -> None: ...

    def parse_int(self) -> None: ...

    def parse_float(self) -> None: ...

    def check_pm(self) -> bool: ...

    def check_conversation(self) -> bool: ...

    def check_fwd(self) -> bool: ...

    def check_platforms(self) -> bool: ...

    def check_attachments(self) -> None: ...

    def check_city(self, city=None) -> None: ...

    def check_mentioned(self) -> None: ...

    def check_non_mentioned(self) -> bool: ...

    def handle_menu(self, menu: list, arg: str) -> Callable: ...

    def _get_help_button_keyboard(self) -> None: ...

    def __eq__(self, other) -> bool: ...

    def __hash__(self) -> str: ...

    def __str__(self) -> str: ...


class AcceptExtraProtocol:
    @staticmethod
    def accept_extra(event) -> bool: ...
