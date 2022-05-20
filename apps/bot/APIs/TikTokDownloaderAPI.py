import requests

from petrovich.settings import env


class TikTokDownloaderAPI:
    HEADERS = {
        "X-RapidAPI-Host": "tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com",
        "X-RapidAPI-Key": env.str("RAPID_API_KEY"),
    }
    URL = "https://tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com/vid/index"

    def get_video_url(self, url):
        return requests.get(self.URL, params={'url': url}, headers=self.HEADERS).json()['video'][0]
