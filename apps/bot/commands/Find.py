from apps.bot.APIs.QwantAPI import QwantAPI
from apps.bot.classes.common.CommonCommand import CommonCommand


class Find(CommonCommand):
    def __init__(self):
        names = ["поиск", "найди", "найти", "ищи", "искать"]
        help_text = "Поиск  - ищет информацию по картинкам"
        detail_help_text = "Поиск (запрос) - ищет информацию по картинкам"

        super().__init__(names, help_text, detail_help_text, args=1, platforms=['vk','tg'])

    def start(self):
        self.bot.set_activity(self.event.peer_id)

        query = self.event.original_args
        count = 5

        qwant_api = QwantAPI()
        urls = qwant_api.get_urls(query)

        if len(urls) == 0:
            return "Ничего не нашёл"
        attachments = self.bot.upload_photos(urls, count)
        if len(attachments) == 0:
            return "Ничего не нашёл 2"
        return {'msg': f'Результаты по запросу "{query}"', 'attachments': attachments}
