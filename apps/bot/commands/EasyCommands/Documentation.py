from apps.bot.classes.common.CommonCommand import CommonCommand


class Documentation(CommonCommand):
    names = ["документация", "дока"]
    help_text = "Документация - ссылка на документацию"

    def start(self):
        url = 'https://vk.com/@igor_petrovich_ksta-instrukciya-po-ispolzovaniu'
        return {'msg': url, 'attachments': [url]}
