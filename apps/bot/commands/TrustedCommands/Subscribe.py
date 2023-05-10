import requests
from bs4 import BeautifulSoup

from apps.bot.APIs.TheHoleAPI import TheHoleAPI
from apps.bot.APIs.WASDAPI import WASDAPI
from apps.bot.APIs.YoutubeVideoAPI import YoutubeVideoAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.classes.consts.Exceptions import PWarning
from apps.service.models import Subscribe as SubscribeModel

MAX_USER_SUBS_COUNT = 3


class Subscribe(Command):
    name = "подписка"
    names = ['подписки']
    help_text = "создаёт подписку на каналы"
    help_texts = [
        "добавить (ссылка на канал) - создаёт подписку на канал. Бот пришлёт тебе новое видео с канала",
        "удалить (название канала) - удаляет вашу подписку на канал (если в конфе, то только по конфе, в лс только по лс)",
        "все - пришлёт активные подписки",
        "конфа - пришлёт активные подписки по конфе"
    ]
    help_texts_extra = \
        "Проверка новых видео проходит каждый час. Стримов - 5 минут\n" \
        "Админ конфы может удалять подписки в конф"
    args = 1
    platforms = [Platform.TG]
    access = Role.TRUSTED

    THE_HOLE_URL = "the-hole.tv"
    YOUTUBE_URL = "youtube.com"
    WASD_URL = "wasd.tv"

    def start(self):
        arg0 = self.event.message.args[0]
        menu = [
            [['добавить', 'подписаться', 'подписка'], self.menu_add],
            [['удалить', 'отписаться', 'отписка'], self.menu_delete],
            [['все', 'всё'], self.menu_subs],
            [['конфа'], self.menu_conference],
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    def menu_add(self):
        self.check_args(2)
        url = self.event.message.args_case[1]

        if self.YOUTUBE_URL in url:
            channel_id, title, date, last_video_id, is_stream = self.menu_add_youtube(url)
            service = SubscribeModel.SERVICE_YOUTUBE
        elif self.THE_HOLE_URL in url:
            channel_id, title, date, last_video_id, is_stream = self.menu_add_the_hole(url)
            service = SubscribeModel.SERVICE_THE_HOLE
        elif self.WASD_URL in url:
            channel_id, title, date, last_video_id, is_stream = self.menu_add_wasd(url)
            service = SubscribeModel.SERVICE_WASD
        else:
            raise PWarning("Незнакомый сервис. Доступные: \nЮтуб, The-Hole")

        if self.event.chat:
            existed_sub = SubscribeModel.objects.filter(chat=self.event.chat, channel_id=channel_id)
        else:
            existed_sub = SubscribeModel.objects.filter(chat__isnull=True, channel_id=channel_id)
        if existed_sub.exists():
            raise PWarning(f"Ты уже и так подписан на канал {existed_sub.first().title}")

        sub = SubscribeModel(
            author=self.event.user,
            chat=self.event.chat,
            channel_id=channel_id,
            title=title,
            date=date,
            service=service,
            last_video_id=last_video_id,
            is_stream=is_stream,
            message_thread_id=self.event.message_thread_id
        )
        sub.save()
        return f'Подписал на канал {title}'

    @staticmethod
    def menu_add_youtube(url):
        response = requests.get(url)
        bs4 = BeautifulSoup(response.content, 'html.parser')
        channel_id = bs4.find_all('link', {'rel': 'canonical'})[0].attrs['href'].split('/')[-1]

        youtube_info = YoutubeVideoAPI()
        youtube_data = youtube_info.get_last_video(channel_id)

        title = youtube_data['title']
        date = youtube_data['last_video']['date']

        is_stream = False

        return channel_id, title, date, None, is_stream

    @staticmethod
    def menu_add_the_hole(url):
        the_hole_api = TheHoleAPI()
        the_hole_api.parse_channel(url)

        is_stream = False

        return the_hole_api.channel_id, the_hole_api.title, None, the_hole_api.last_video_id, is_stream

    @staticmethod
    def menu_add_wasd(url):
        wasd_api = WASDAPI()
        wasd_api.parse_channel(url)
        is_stream = True

        return wasd_api.channel_id, wasd_api.title, None, None, is_stream

    def menu_delete(self):
        self.check_args(2)
        channel_filter = self.event.message.args[1:]
        sub = self.get_sub(channel_filter, True)
        sub_title = sub.title
        sub.delete()
        return f"Удалил подписку на канал {sub_title}"

    def menu_subs(self):
        return self.get_subs()

    def menu_conference(self):
        self.check_conversation()
        return self.get_subs(conversation=True)

    def get_sub(self, filters, for_delete=False):
        if self.event.chat:
            subs = SubscribeModel.objects.filter(chat=self.event.chat)
            if self.event.chat.admin != self.event.user:
                subs = subs.filter(author=self.event.user)
        else:
            subs = SubscribeModel.objects.filter(author=self.event.user)
            if for_delete:
                subs = subs.filter(chat__isnull=True)

        for _filter in filters:
            subs = subs.filter(title__icontains=_filter)

        subs_count = subs.count()
        if subs_count == 0:
            raise PWarning("Не нашёл :(")
        elif subs_count == 1:
            return subs.first()
        else:
            filters_str = " ".join(filters)
            for sub in subs:
                if sub.title == filters_str:
                    return sub
            subs = subs[:10]
            subs_titles = [yt_sub.title for yt_sub in subs]
            subs_titles_str = ";\n".join(subs_titles)

            msg = f"Нашёл сразу {subs_count}. уточните:\n\n" \
                  f"{subs_titles_str}" + '.'
            if subs_count > 10:
                msg += "\n..."
            raise PWarning(msg)

    def get_subs(self, conversation=False):
        if conversation:
            subs = SubscribeModel.objects.filter(chat=self.event.chat)
        else:
            subs = SubscribeModel.objects.filter(author=self.event.user)
            if self.event.chat:
                subs = subs.filter(chat=self.event.chat)
        if subs.count() == 0:
            raise PWarning("Нет активных подписок")

        subs_titles_str = ""
        for sub in subs:
            subs_titles_str += f"[{sub.get_service_display()}] {sub.title}"
            if not conversation and sub.chat:
                subs_titles_str += f" (конфа - {sub.chat})"
            subs_titles_str += '\n'

        return subs_titles_str
