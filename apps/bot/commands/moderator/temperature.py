from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.do_the_linux_command import do_the_linux_command


class Temperature(Command):
    name = "температура"
    names = ['темп']

    help_text = HelpText(
        commands_text="температуры сервера"
    )

    access = Role.MODERATOR

    def start(self) -> ResponseMessage:
        command = "sensors"
        output = do_the_linux_command(command)
        answer = []

        for row in output.split('\n'):
            index = row.find('(')
            if index != -1:
                row = row[:index].strip()
            answer.append(row)
        answer = "\n".join(answer)

        return ResponseMessage(ResponseMessageItem(text=answer))
