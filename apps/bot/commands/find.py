from apps.bot.api.google_custom_search import GoogleCustomSearch
from apps.bot.classes.bots.tg import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Platform
from apps.bot.classes.const.exceptions import PWarning, PError
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Find(Command):
    name = "найди"
    names = ["поиск", "найти", "ищи", "искать", "хуизфакинг", "вхуизфакинг"]
    help_text = "ищет информацию по картинкам в гугле"
    help_texts = ["(запрос) - ищет информацию по картинкам в гугле"]
    args = 1
    platforms = [Platform.TG]

    bot: TgBot

    def start(self) -> ResponseMessage:
        query = self.event.message.args_str

        photo_results = self.get_photo_results(query)
        return photo_results

    def get_photo_results(self, query):
        count = 5

        gcs_api = GoogleCustomSearch()
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
            except (PError, Exception):
                continue
            if len(attachments) == count:
                break
        self.bot.stop_activity_thread()
        if len(attachments) == 0:
            raise PWarning("Ничего не нашёл по картинкам")
        answer = f"Результаты по запросу '{query}'"
        return ResponseMessage(ResponseMessageItem(text=answer, attachments=attachments))
