from apps.bot.classes.common.CommonCommand import CommonCommand


class StartLada(CommonCommand):
    name = "заведи"
    names = ["завести"]

    def start(self):
        if self.event.args:
            who = self.event.original_args
            return ["уи ви ви ви ви ви ви ви", f'завожу {who}']

        return "уи ви ви ви ви ви ви ви"
