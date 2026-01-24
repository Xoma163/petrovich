from apps.commands.command import Command
from apps.bot.consts import Role
from apps.shared.exceptions import PWarning
from apps.commands.help_text import HelpTextItem, HelpText, HelpTextArgument
from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import get_random_int, random_event


class Random(Command):
    name = "рандом"
    names = ["ранд"]

    help_text = HelpText(
        commands_text="рандомное число в заданном диапазоне",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextArgument(None, "рандомное число в диапазоне [0:1]"),
                HelpTextArgument("[N]", "рандомное число в заданном диапазоне [1:N]"),
                HelpTextArgument("[N,M]", "рандомное число в заданном диапазоне [N:M]"),
                HelpTextArgument("[Слово_1, Слово_2, ...]", "рандомное слово среди аргументов")
            ])
        ]
    )

    def start(self) -> ResponseMessage:
        # Если аргументов нет или они целочисленные
        try:
            self.int_args = [0, 1]
            self.parse_int()
            rand_int = self._get_random_int()
            answer = str(rand_int)
        # Если текст
        except PWarning:
            answer = random_event(self.event.message.args_case)
        return ResponseMessage(ResponseMessageItem(text=answer))

    def _get_random_int(self):
        if self.event.message.args:
            if len(self.event.message.args) == 2:
                int1 = self.event.message.args[0]
                int2 = self.event.message.args[1]
            else:
                int1 = 1
                int2 = self.event.message.args[0]
                self.check_number_arg_range(int2, 2)
        else:
            int1 = 0
            int2 = 1

        if int1 > int2:
            int1, int2 = int2, int1

        return get_random_int(int1, int2)
