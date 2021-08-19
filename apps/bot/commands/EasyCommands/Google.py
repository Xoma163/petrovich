from urllib.parse import quote

from apps.bot.classes.common.CommonCommand import CommonCommand


class Google(CommonCommand):
    name = "гугл"
    help_text = "формирует ссылку в гугл"
    args = 1

    def start(self):
        return f"https://www.google.com/search?q={quote(self.event.original_args)}"
