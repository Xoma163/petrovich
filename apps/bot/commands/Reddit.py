from urllib.parse import urlparse

from apps.bot.APIs.RedditVideoDownloader import RedditVideoSaver
from apps.bot.classes.Consts import Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand

REDDIT_URLS = ["www.reddit.com"]

class Reddit(CommonCommand):
    name = "реддит"
    names = ["reddit"]
    help_text = "присылает видео с реддита"
    help_texts = ["(ссылка на реддит с видео) - присылает видео из поста с реддита"]
    platforms = [Platform.TG]



    def accept(self, event):
        if urlparse(event.command).hostname in REDDIT_URLS:
            return True
        if event.fwd:
            if urlparse(event.fwd[0]['text']).hostname in REDDIT_URLS:
                return True
        return super().accept(event)

    def start(self):
        if self.event.command in self.full_names:
            if self.event.args:
                url = self.event.args[0]
            elif self.event.fwd:
                url = self.event.fwd[0]['text']
            else:
                raise PWarning("Для работы команды требуются аргументы или пересылаемые сообщения")
        else:
            url = self.event.command

        if urlparse(url).hostname not in REDDIT_URLS:
            raise PWarning("Не reddit ссылка в аргументах")

        rvs = RedditVideoSaver()
        self.bot.set_activity(self.event.peer_id,'typing')
        video = rvs.get_video_from_post(url)
        attachments = [self.bot.upload_video(video)]
        return {
            'attachments': attachments
        }
