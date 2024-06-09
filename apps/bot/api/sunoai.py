import re

import requests
from bs4 import BeautifulSoup


class SunoAIData:

    def __init__(self, title, download_url, cover_url, song_text, author=None):
        self.title = title
        self.download_url = download_url
        self.cover_url = cover_url
        self.song_text = song_text
        self.author = author
        self.format = download_url.rsplit('.')[-1]


class SunoAI:

    @staticmethod
    def get_info(url) -> SunoAIData:
        r = requests.post(url)
        bs4 = BeautifulSoup(r.content, 'html.parser')
        title = bs4.find('meta', attrs={'property': 'og:title'}).attrs['content'].replace(" | Suno", "")
        audio_url = bs4.find('meta', attrs={'property': 'og:audio'}).attrs['content']
        cover_url = bs4.find('meta', attrs={'property': 'og:image'}).attrs['content']

        author = re.findall(r'\\"display_name\\":\\"(.*)\\",\\"handle', r.text)
        author = author[0] if author else None
        title = title.replace(f"by @{author.lower()}", '').strip()
        text = None

        return SunoAIData(
            title,
            audio_url,
            cover_url,
            text,
            author
        )
