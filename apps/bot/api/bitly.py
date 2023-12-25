from apps.bot.api.handler import API
from petrovich.settings import env


class BitLy(API):
    URL = "https://api-ssl.bitly.com/v4/shorten/"
    HEADERS = {
        "Authorization": f"Bearer {env.str('BITLY_TOKEN')}",
        "Content-Type": "application/json"
    }

    def get_short_link(self, long_url: str) -> str:
        params = {
            "domain": "bit.ly",
            "long_url": long_url
        }
        r = self.requests.post(self.URL, json=params, headers=self.HEADERS).json()

        return r['link']
