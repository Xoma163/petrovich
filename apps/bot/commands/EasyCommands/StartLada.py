from apps.bot.classes.common.CommonCommand import CommonCommand


class StartLada(CommonCommand):
    names = ["завести", "заведи"]

    def start(self):
        if self.event.args:
            who = self.event.original_args
            return ["уи ви ви ви ви ви ви ви", f'завожу {who}']

        return "уи ви ви ви ви ви ви ви"
