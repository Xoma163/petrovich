from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem
from apps.bot.utils.DoTheLinuxComand import do_the_linux_command


class Temperature(Command):
    name = "температура"
    names = ['темп']
    help_text = "температуры сервера"
    access = Role.MODERATOR

    def start(self) -> ResponseMessage:
        command = "sensors"
        output = do_the_linux_command(command)

        find_text = 'Adapter: ISA adapter\nPackage id 0:'
        answer = f"AVG:{output[output.find(find_text) + len(find_text):].replace('(high = +80.0°C, crit = +100.0°C)', '')}"

        return ResponseMessage(ResponseMessageItem(text=answer))
