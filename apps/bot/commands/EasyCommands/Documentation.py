from apps.bot.classes.Command import Command


class Documentation(Command):
    name = "документация"
    names = ["дока"]
    help_text = "ссылка на документацию"

    def start(self):
        # url = 'https://vk.com/@igor_petrovich_ksta-instrukciya-po-ispolzovaniu'
        url = 'https://github.com/Xoma163/petrovich/wiki/1.1-Документация-для-пользователей'
        return {'msg': url, 'attachments': [url]}
