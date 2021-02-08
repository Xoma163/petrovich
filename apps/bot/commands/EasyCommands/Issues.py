from apps.bot.classes.common.CommonCommand import CommonCommand


class Issues(CommonCommand):
    names = ["баги", "ишюс", "ишьюс", "иши"]
    help_text = "Баги - список проблем"

    # ToDo: выводить ишюсы списком просто
    def start(self):
        return "https://github.com/Xoma163/petrovich/issues"
