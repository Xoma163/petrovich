class InstagramAPIDataItem:
    CONTENT_TYPE_IMAGE = 'image'
    CONTENT_TYPE_VIDEO = 'video'

    def __init__(self, content_type: str, download_url: str, thumbnail_url: str | None = None):
        if content_type not in (self.CONTENT_TYPE_IMAGE, self.CONTENT_TYPE_VIDEO):
            raise RuntimeError(f"content_type must be {self.CONTENT_TYPE_IMAGE} or {self.CONTENT_TYPE_VIDEO}")

        self.content_type = content_type
        self.download_url = download_url
        self.thumbnail_url = thumbnail_url


class InstagramAPIData:
    def __init__(self):
        self.items: list[InstagramAPIDataItem] = []
        self.caption: str = ""

    def add_item(self, item: InstagramAPIDataItem):
        self.items.append(item)

    def add_video(self, download_url: str, thumbnail_url: str):
        item = InstagramAPIDataItem(
            content_type=InstagramAPIDataItem.CONTENT_TYPE_VIDEO,
            download_url=download_url,
            thumbnail_url=thumbnail_url
        )
        self.add_item(item)

    def add_image(self, download_url: str):
        item = InstagramAPIDataItem(
            content_type=InstagramAPIDataItem.CONTENT_TYPE_IMAGE,
            download_url=download_url
        )
        self.add_item(item)
