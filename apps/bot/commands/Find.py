from apps.bot.APIs.GoogleCustomSearchAPI import GoogleCustomSearchAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PWarning


class Find(Command):
    name = "найди"
    names = ["поиск", "найти", "ищи", "искать", "хуизфакинг", "вхуизфакинг"]
    help_text = "ищет информацию по картинкам в гугле"
    help_texts = ["(запрос) - ищет информацию по картинкам в гугле"]
    args = 1
    excluded_platforms = [Platform.YANDEX]

    def start(self):
        query = self.event.message.args_str

        try:
            photo_results = self.get_photo_results(query)
        except PWarning as e:
            photo_results = str(e)
        result = [f"Результаты по запросу '{query}'", photo_results]
        return result

    def get_photo_results(self, query):
        count = 5

        gcs_api = GoogleCustomSearchAPI()
        urls = gcs_api.get_images_urls(query)
        if len(urls) == 0:
            raise PWarning("Ничего не нашёл по картинкам")

        attachments = []
        if self.event.platform == Platform.VK:
            attachments = self.bot.upload_photos(urls, count, peer_id=self.event.peer_id)
        elif self.event.platform == Platform.TG:
            for url in urls:
                self.bot.set_activity(self.event.peer_id, ActivitiesEnum.UPLOAD_PHOTO)
                try:
                    attachments.append(self.bot.upload_image_to_tg_server(url))
                except PWarning:
                    continue
                if len(attachments) == count:
                    break
        else:
            attachments = self.bot.upload_photos(urls, 5)
        if len(attachments) == 0:
            raise PWarning("Ничего не нашёл по картинкам")
        return {'attachments': attachments}
