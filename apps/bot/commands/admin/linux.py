from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.do_the_linux_command import do_the_linux_command


class Linux(Command):
    name = "линукс"
    names = ["linux", "консоль", "терминал"]

    help_text = HelpText(
        commands_text="запускает любую команду на сервере",
        help_texts=[
            HelpTextItem(Role.ADMIN, [
                HelpTextItemCommand("(команда)", "запускает любую команду на сервере")
            ])
        ]
    )

    access = Role.ADMIN
    args = 1

    def start(self) -> ResponseMessage:
        answer = do_the_linux_command(self.event.message.args_str)
        return ResponseMessage(ResponseMessageItem(text=answer))
