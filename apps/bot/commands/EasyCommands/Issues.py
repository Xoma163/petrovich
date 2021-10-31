from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform


class Issues(Command):
    name = "баги"
    name_tg = 'issues'
    names = ["ишюс", "ишьюс", "иши"]

    help_text = "список проблем"

    def start(self):
        url = "https://github.com/Xoma163/petrovich/issues"
        if self.event.platform == Platform.TG:
            return {'text': f"[Ишюс]({url})", 'parse_mode':'markdown'}
        return url
