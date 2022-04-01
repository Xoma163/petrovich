from apps.bot.classes.Command import Command


class StartLada(Command):
    name = "заведи"
    names = ["завести"]

    def start(self):
        if self.event.message.args:
            who = self.event.message.args_str_case
            return ["уи ви ви ви ви ви ви ви", f'завожу {who}']

        return "уи ви ви ви ви ви ви ви"
