from apps.bot.classes.Command import Command


class Issues(Command):
    name = "баги"
    name_tg = 'issues'
    names = ["ишюс", "ишьюс", "иши"]

    help_text = "список проблем"

    def start(self):
        url = "https://github.com/Xoma163/petrovich/issues"
        return self.bot.get_formatted_url("Ишюс", url)
