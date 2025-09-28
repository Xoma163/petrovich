import re

from apps.bot.api.media.reddit import Reddit
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.commands.media.service import MediaServiceResponse, MediaService
from apps.bot.utils.utils import retry, markdown_to_html


class RedditService(MediaService):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.service = Reddit()

    @retry(3, Exception, sleep_time=2, except_exceptions=(PWarning,))
    def get_content_by_url(self, url: str) -> MediaServiceResponse:
        reddit_data = self.service.get_post_data(url)
        result_text = self.service.title

        if self.service.is_gif:
            attachments = [self.bot.get_gif_attachment(
                reddit_data,
                peer_id=self.event.peer_id,
                filename=self.service.filename
            )]
        elif self.service.is_image or self.service.is_images or self.service.is_gallery:
            attachments = [self.bot.get_photo_attachment(
                att,
                peer_id=self.event.peer_id,
                filename=self.service.filename,
                send_chat_action=False
            ) for att in reddit_data]
        elif self.service.is_video:
            attachments = [self.bot.get_video_attachment(
                reddit_data,
                peer_id=self.event.peer_id,
                filename=self.service.filename
            )]
        elif self.service.is_text or self.service.is_link:
            text = reddit_data
            all_photos = []
            text = text \
                .replace("&#x200B;", "") \
                .replace("&amp;#x200B;", "") \
                .replace("&amp;", "&") \
                .replace(" ", " ") \
                .strip()
            text = markdown_to_html(text, self.bot)
            regexps_with_static = (
            (r"https.*player", "Видео"), (r"https://preview\.redd\.it/(?:\w|\d|\.|\?|\=|&)*", "Фото"))
            for regexp, _text in regexps_with_static:
                p = re.compile(regexp)
                for item in reversed(list(p.finditer(text))):
                    start_pos = item.start()
                    end_pos = item.end()
                    link = text[start_pos:end_pos]
                    if _text == "Фото":
                        all_photos.append(link)
                    if text[start_pos - 9:start_pos] == "<a href=\"":
                        continue
                    tg_url = self.bot.get_formatted_url(_text, link)
                    text = text[:start_pos] + tg_url + text[end_pos:]

            all_photos = reversed(all_photos)
            attachments = [
                self.bot.get_photo_attachment(
                    photo,
                    peer_id=self.event.peer_id,
                    filename=self.service.filename,
                    send_chat_action=False
                )
                for photo in all_photos
            ]
            result_text = f"{self.service.title}\n\n{text}"
        else:
            raise PWarning("Я хз чё за контент")
        return MediaServiceResponse(text=result_text, attachments=attachments, need_to_wrap_html_tags=False)

    @classmethod
    def urls(cls) -> list[str]:
        return ["www.reddit.com", "reddit.com"]
