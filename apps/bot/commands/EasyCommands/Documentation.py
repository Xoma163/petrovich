from apps.bot.classes.common.CommonCommand import CommonCommand


class Documentation(CommonCommand):
    def __init__(self):
        names = ["документация", "дока"]
        help_text = "Документация - ссылка на документацию"
        super().__init__(names, help_text)

    def start(self):
        url = 'https://vk.com/@igor_petrovich_ksta-instrukciya-po-ispolzovaniu'
        return {'msg': url, 'attachments': [url]}
