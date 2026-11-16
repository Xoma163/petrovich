import re

import requests
from bs4 import BeautifulSoup

from apps.connectors.parsers.media_command.data import AudioData
from apps.shared.exceptions import PWarning


class SunoAIData:
    def __init__(self, title, download_url, thumbnail_url, song_text, author=None):
        self.title = title
        self.download_url = download_url
        self.thumbnail_url = thumbnail_url
        self.song_text = song_text
        self.author = author
        self.format = download_url.rsplit(".")[-1]


class SunoAI:
    @staticmethod
    def get_info(url) -> AudioData:
        r = requests.post(url)
        bs4 = BeautifulSoup(r.content, "html.parser")
        metadata = {}
        for property_name in ("og:title", "og:audio", "og:image"):
            tag = bs4.find("meta", attrs={"property": property_name})
            metadata[property_name] = tag.get("content") if tag is not None else None
        audio_url = metadata["og:audio"]
        if not audio_url:
            raise PWarning("Suno не вернул ссылку на аудио. Проверьте ссылку и доступ к композиции")
        title = (metadata["og:title"] or "Аудио из Suno").replace(" | Suno", "")
        thumbnail_url = metadata["og:image"]

        author = re.findall(r'"display_name\\\"\:\\\"((?:\\\\.|[^"\\])*)\\\"', r.text)
        author = author[-1] if author else None
        # title = title.replace(f"by @{author.lower()}", '').strip()

        match = re.search(r"prompt\\\"\:\\\"(.*?)\\\"\,\\\"edited", r.text)
        text = "\n".join(match.group(1).split(r"\\n")) if match else None

        return AudioData(
            title=title,
            download_url=audio_url,
            thumbnail_url=thumbnail_url,
            text=text,
            artists=author,
        )
