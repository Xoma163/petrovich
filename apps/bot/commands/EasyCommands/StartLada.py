from apps.bot.classes.common.CommonCommand import CommonCommand


class StartLada(CommonCommand):
    def __init__(self):
        names = ["завести", "заведи"]
        super().__init__(names)

    def start(self):
        if self.event.args:
            who = self.event.original_args
            return ["уи ви ви ви ви ви ви ви", f'завёл {who}']

        return "уи ви ви ви ви ви ви ви"
