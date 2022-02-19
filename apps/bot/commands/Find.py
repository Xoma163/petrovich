from apps.bot.APIs.GoogleCustomSearchAPI import GoogleCustomSearchAPI
from apps.bot.APIs.SpotifyAPI import SpotifyAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.utils import get_tg_formatted_url


class Find(Command):
    name = "найди"
    names = ["поиск", "найти", "ищи", "искать", "хуизфакинг", "вхуизфакинг"]
    help_text = "ищет информацию по картинкам в гугле и музыке в спотифае"
    help_texts = ["(запрос) - ищет информацию по картинкам в гугле и музыке в спотифае"]
    args = 1
    excluded_platforms = [Platform.YANDEX]

    def start(self):
        query = self.event.message.args_str

        try:
            photo_results = self.get_photo_results(query)
        except PWarning as e:
            photo_results = str(e)
        try:
            music_results = self.get_music_results(query)
        except PWarning as e:
            music_results = str(e)
        result = [f"Результаты по запросу '{query}'", photo_results, music_results]
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

    def get_music_results(self, query):
        spotify_api = SpotifyAPI()
        musics = spotify_api.search_music(query, limit=5)
        if not musics:
            raise PWarning("Ничего не нашёл по музыке")
        message = []
        for music_info in musics:
            music = f"{', '.join(music_info['artists'])} — {music_info['name']}"
            if self.event.platform == Platform.TG:
                message.append(get_tg_formatted_url(music, music_info['url']))
            else:
                message.append(f"{music} ({music_info['url']})")
        return {'text': "\n".join(message)}
