from apps.bot.classes.Command import Command


class Documentation(Command):
    name = "документация"
    names = ["дока"]
    help_text = "ссылка на документацию"

    def start(self):
        url = 'https://github.com/Xoma163/petrovich/wiki/1.1-Документация-для-пользователей'
        return self.bot.get_formatted_url("Документация", url)
