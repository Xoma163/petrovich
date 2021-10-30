import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from apps.bot.classes.bots.Bot import get_bot_by_platform
from apps.bot.models import Users
from apps.service.models import Service


class Command(BaseCommand):
    URL = "https://gks1frunze.ru"

    def add_arguments(self, parser):
        parser.add_argument('chat_id', nargs='+', type=str, help='chat_id')

    def handle(self, *args, **options):
        chat_id = options['chat_id'][0]
        pasha = Users.objects.get(user_id=chat_id)
        bot = get_bot_by_platform(pasha.get_platform_enum())

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
        for news in news_to_send:
            msgs.append(self.parse_news(f"{self.URL}{news.attrs['href']}"))

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
        return f"{news_content}\n\n{news_url}"

    @staticmethod
    def get_news_id(x):
        return int(x.attrs['href'].split('/')[-2])
