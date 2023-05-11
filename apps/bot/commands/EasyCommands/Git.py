from apps.bot.classes.Command import Command


class Git(Command):
    name = "гит"
    names = ["гитхаб"]
    name_tg = 'github'

    help_text = "ссылка на гитхаб"

    def start(self):
        url = 'https://github.com/Xoma163/petrovich/'

        return self.bot.get_formatted_url("Гитхаб", url)
