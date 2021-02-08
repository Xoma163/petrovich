import json

import requests
from bs4 import BeautifulSoup

from apps.bot.classes.Consts import Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import check_command_time


class Find(CommonCommand):
    names = ["поиск", "найди", "найти", "ищи", "искать"]
    help_text = "Поиск  - ищет информацию по картинкам"
    detail_help_text = "Поиск (запрос) - ищет информацию по картинкам"
    args = 1
    platforms = [Platform.VK, Platform.TG]

    def start(self):
        # В связи с тем, что парсим страницы
        check_command_time("find_images", 15)
        self.bot.set_activity(self.event.peer_id)

        query = self.event.original_args
        count = 5

        content = requests.get(
            f'https://yandex.ru/images/search?text={query}',
            # Кука на безопасный поиск
            cookies={
                'yp': '1929040280.sp.family%3A2#1613420360.szm.1%3A1920x1080%3A1920x969#1612901961.nps.7769161127%3Aclose'
            }).content
        bs4 = BeautifulSoup(content)
        urls = [json.loads(x.attrs['data-bem'])['serp-item']['img_href'] for x in bs4.select('.serp-item')]

        # qwant_api = QwantAPI()
        # urls = qwant_api.get_urls(query)
        #
        if len(urls) == 0:
            raise PWarning("Ничего не нашёл")
        attachments = self.bot.upload_photos(urls, count)
        if len(attachments) == 0:
            raise PWarning("Ничего не нашёл 2")
        return {'msg': f'Результаты по запросу "{query}"', 'attachments': attachments}
