from apps.bot.api.handler import API


class FuckingGreatAdvice(API):
    URL = "https://fucking-great-advice.ru/api/random"

    def get_advice(self) -> str:
        r = self.requests.get(self.URL).json()

        return r['text']
