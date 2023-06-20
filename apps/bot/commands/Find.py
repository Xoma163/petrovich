from apps.bot.APIs.GoogleCustomSearchAPI import GoogleCustomSearchAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PWarning, PError
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment


class Find(Command):
    name = "найди"
    names = ["поиск", "найти", "ищи", "искать", "хуизфакинг", "вхуизфакинг"]
    help_text = "ищет информацию по картинкам в гугле"
    help_texts = ["(запрос) - ищет информацию по картинкам в гугле"]
    args = 1
    platforms = [Platform.TG]

    bot: TgBot

    def start(self):
        query = self.event.message.args_str

        try:
            photo_results = self.get_photo_results(query)
        except PWarning as e:
            photo_results = str(e)
        return photo_results

    def get_photo_results(self, query):
        count = 5

        gcs_api = GoogleCustomSearchAPI()
        urls = gcs_api.get_images_urls(query)
        if len(urls) == 0:
            raise PWarning("Ничего не нашёл по картинкам")

        attachments = []
        self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.UPLOAD_PHOTO)
        for url in urls:
            try:
                att = PhotoAttachment()
                att.public_download_url = url
                att.set_file_id()
                attachments.append(att)
            except PError:
                continue
            if len(attachments) == count:
                break
        self.bot.stop_activity_thread()
        if len(attachments) == 0:
            raise PWarning("Ничего не нашёл по картинкам")
        return {'text': f"Результаты по запросу '{query}'", 'attachments': attachments}
