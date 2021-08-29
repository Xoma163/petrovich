from apps.bot.APIs.RedditVideoDownloader import RedditVideoSaver
from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand


class Reddit(CommonCommand):
    name = "реддит"
    names = ["reddit"]
    help_text = "присылает видео с реддита"
    help_texts = ["(ссылка на реддит с видео) - присылает видео из поста с реддита"]
    args_or_fwd = 1
    platforms = [Platform.TG]

    def start(self):
        if self.event.args:
            url = self.event.args[0]
        else:
            url = self.event.fwd[0]['text']
        rvs = RedditVideoSaver()
        video = rvs.get_video_from_post(url)
        attachments = [self.bot.upload_video(video)]
        return {
            'attachments': attachments
        }
