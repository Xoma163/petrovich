from apps.bot.APIs.GoogleCustomSearchAPI import GoogleCustomSearchAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PWarning


class Find(Command):
    name = "найди"
    names = ["поиск", "найти", "ищи", "искать", "хуизфакинг", "вхуизфакинг"]
    help_text = "ищет информацию по картинкам"
    help_texts = ["(запрос) - ищет информацию по картинкам"]
    args = 1
    platforms = [Platform.VK, Platform.TG]

    def start(self):
        query = self.event.message.args_str
        count = 5

        gcs_api = GoogleCustomSearchAPI()
        urls = gcs_api.get_images_urls(query)
        if len(urls) == 0:
            raise PWarning("Ничего не нашёл")
        attachments = self.bot.upload_photos(urls, count, peer_id=self.event.peer_id)
        if len(attachments) == 0:
            raise PWarning("Ничего не нашёл 2")

        msgs = [f'Результаты по запросу "{query}"']
        for att in attachments:
            msgs.append({'attachments': [att]})
        return msgs
