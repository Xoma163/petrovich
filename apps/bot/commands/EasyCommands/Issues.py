from apps.bot.classes.Command import Command


class Issues(Command):
    name = "баги"
    names = ["ишюс", "ишьюс", "иши"]
    help_text = "список проблем"

    def start(self):
        return "https://github.com/Xoma163/petrovich/issues"
