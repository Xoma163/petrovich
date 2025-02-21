from apps.bot.classes.messages.attachments.photo import PhotoAttachment


class ThumbnailMixin:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.thumbnail_url: str | None = None
        self.thumbnail: PhotoAttachment | None = None
        self.use_proxy_on_download_thumbnail: bool = False

    def set_thumbnail(self, content: bytes = None):
        from apps.bot.utils.utils import make_thumbnail

        if self.thumbnail_url is None and content is None:
            return

        thumb_file = PhotoAttachment()
        if content:
            thumb_file.parse(content)
        else:
            thumb_file.parse(self.thumbnail_url, guarantee_url=True)

        thumbnail = make_thumbnail(thumb_file, max_size=None, use_proxy=self.use_proxy_on_download_thumbnail)
        thumbnail_att = PhotoAttachment()
        thumbnail_att.parse(thumbnail)
        self.thumbnail = thumbnail_att
