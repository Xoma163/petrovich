from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform


class Documentation(Command):
    name = "документация"
    names = ["дока"]
    help_text = "ссылка на документацию"

    def start(self):
        url = 'https://github.com/Xoma163/petrovich/wiki/1.1-Документация-для-пользователей'
        if self.event.platform == Platform.TG:
            return {'text': f"[Документация]({url})", 'parse_mode':'markdown'}
        return url
