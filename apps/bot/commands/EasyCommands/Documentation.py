from apps.bot.classes.common.CommonCommand import CommonCommand


class Documentation(CommonCommand):
    name = "документация"
    names = ["дока"]
    help_text = "ссылка на документацию"

    def start(self):
        url = 'https://vk.com/@igor_petrovich_ksta-instrukciya-po-ispolzovaniu'
        return {'msg': url, 'attachments': [url]}
