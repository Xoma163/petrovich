import re
from urllib.parse import urlparse

from apps.bot.core.messages.attachments.attachment import Attachment


class LinkAttachment(Attachment):
    TYPE = "link"

    def __init__(self):
        super().__init__(self.TYPE)
        self.url: str | None = None

    @property
    def is_youtube_link(self):
        return self._check_link(['youtu.be', 'youtube.com'])

    @property
    def is_vk_link(self):
        return self._check_link(["vk.com", "vkvideo.ru"])

    def _check_link(self, urls):
        parsed_url = urlparse(self.url)
        return parsed_url.hostname.replace('www.', '').lower() in urls

    @classmethod
    def parse_link(cls, text):
        regexp = r"(http|ftp|https|tg)(://)([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])"
        r = re.compile(regexp)
        res = r.findall(text)
        return ["".join(x) for x in res]
