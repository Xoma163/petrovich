from apps.bot.classes.common.CommonCommand import CommonCommand


class StartLada(CommonCommand):
    name = "заведи"
    names = ["завести"]

    def start(self):
        if self.event.message.args:
            who = self.event.message.args_str
            return ["уи ви ви ви ви ви ви ви", f'завожу {who}']

        return "уи ви ви ви ви ви ви ви"
