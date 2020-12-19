from apps.bot.classes.common.CommonCommand import CommonCommand


class Issues(CommonCommand):
    def __init__(self):
        names = ["баги", "ишюс", "ишьюс", "иши"]
        help_text = "Баги - список проблем"
        super().__init__(names, help_text)

    # ToDo: выводить ишюсы списком просто
    def start(self):
        return "https://github.com/Xoma163/petrovich/issues"
