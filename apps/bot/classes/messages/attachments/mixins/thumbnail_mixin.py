from apps.bot.classes.messages.attachments.photo import PhotoAttachment


class ThumbnailMixin:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.thumbnail_url: str | None = None
        self.thumbnail: PhotoAttachment | None = None

    def set_thumbnail(self):
        from apps.bot.utils.utils import make_thumbnail

        if self.thumbnail_url is None:
            return
        thumb_file = PhotoAttachment()
        thumb_file.parse(self.thumbnail_url, guarantee_url=True)

        thumbnail = make_thumbnail(thumb_file)
        thumbnail_att = PhotoAttachment()
        thumbnail_att.parse(thumbnail)
        self.thumbnail = thumbnail_att
