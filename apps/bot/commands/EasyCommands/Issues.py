from apps.bot.classes.common.CommonCommand import CommonCommand


class Issues(CommonCommand):
    name = "баги"
    names = ["ишюс", "ишьюс", "иши"]
    help_text = "список проблем"

    def start(self):
        return "https://github.com/Xoma163/petrovich/issues"
