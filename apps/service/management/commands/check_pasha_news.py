import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.models import User
from apps.service.models import Service


class Command(BaseCommand):
    URL = "https://gks1frunze.ru"

    def add_arguments(self, parser):
        parser.add_argument('chat_id', nargs='+', type=str, help='chat_id')

    def handle(self, *args, **options):
        chat_id = options['chat_id'][0]
        pasha = User.objects.get(user_id=chat_id)

        pasha_news_last_id_entity, created = Service.objects.get_or_create(
            name='pasha_news_last_id',
            defaults={'value': 0}
        )
        pasha_news_last_id = int(pasha_news_last_id_entity.value)
        content = requests.get(f"{self.URL}/news").content
        bs4 = BeautifulSoup(content, "html.parser")
        news = list(bs4.select(".news-list > .row > a"))
        if created:
            last_news_id = self.get_news_id(news[0])
            pasha_news_last_id_entity.value = last_news_id
            pasha_news_last_id_entity.save()
            return

        news_to_send = list(filter(lambda x: self.get_news_id(x) > pasha_news_last_id, news))
        msgs = []
        bot = TgBot()
        for news in news_to_send:
            news_content, news_url, news_title = self.parse_news(f"{self.URL}{news.attrs['href']}")
            text = f'{bot.get_formatted_url(news_title, news_url)}\n\n{news_content}'
            msgs.append(text)
        if not msgs:
            return
        last_news_id = self.get_news_id(news_to_send[0])
        pasha_news_last_id_entity.value = last_news_id
        pasha_news_last_id_entity.save()

        for msg in msgs:
            bot.parse_and_send_msgs(msg, pasha.user_id)

    @staticmethod
    def parse_news(news_url):
        content = requests.get(news_url).content
        bs4 = BeautifulSoup(content, "html.parser")
        news_content = bs4.select(".news-detail .col-lg-9")[0].text.strip()
        news_title = bs4.select("h1")[0].text.strip()
        if news_title in news_content.split('\n')[0]:
            news_content = "\n".join(news_content.split("\n")[1:])
        return news_content, news_url, news_title

    @staticmethod
    def get_news_id(x):
        return int(x.attrs['href'].split('/')[-2])
