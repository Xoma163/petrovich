from apps.bot.APIs.GoogleCustomSearchAPI import GoogleCustomSearchAPI
from apps.bot.classes.Consts import Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand


class Find(CommonCommand):
    name = "найди"
    names = ["поиск", "найти", "ищи", "искать", "хуизфакинг", "вхуизфакинг"]
    help_text = "ищет информацию по картинкам"
    help_texts = ["(запрос) - ищет информацию по картинкам"]
    args = 1
    platforms = [Platform.VK, Platform.TG]

    def start(self):
        self.bot.set_activity(self.event.peer_id)

        query = self.event.original_args
        count = 5

        gcs_api = GoogleCustomSearchAPI()
        urls = gcs_api.get_images_urls(query)
        if len(urls) == 0:
            raise PWarning("Ничего не нашёл")
        attachments = self.bot.upload_photos(urls, count)
        if len(attachments) == 0:
            raise PWarning("Ничего не нашёл 2")

        msgs = [f'Результаты по запросу "{query}"']
        for att in attachments:
            msgs.append({'attachments': [att]})
        return msgs
