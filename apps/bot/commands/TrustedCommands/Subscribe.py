import requests
from bs4 import BeautifulSoup

from apps.bot.APIs.TheHoleAPI import TheHoleAPI
from apps.bot.APIs.VKVideoAPI import VKVideoAPI
from apps.bot.APIs.WASDAPI import WASDAPI
from apps.bot.APIs.YoutubeVideoAPI import YoutubeVideoAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem
from apps.bot.classes.messages.attachments.LinkAttachment import LinkAttachment
from apps.service.models import Subscribe as SubscribeModel

MAX_USER_SUBS_COUNT = 3


class Subscribe(Command):
    name = "подписка"
    names = ['подписки']
    help_text = "создаёт подписку на каналы. Доступные: YouTube, The-Hole, WAST, VK"
    help_texts = [
        "добавить (ссылка на канал) - создаёт подписку на канал. Бот пришлёт тебе новое видео с канала",
        "удалить (название канала) - удаляет вашу подписку на канал (если в конфе, то только по конфе, в лс только по лс)",
        "все - пришлёт активные подписки",
        "конфа - пришлёт активные подписки по конфе"
    ]
    help_texts_extra = \
        "Проверка новых видео проходит каждые 10 минут. Стримов - 5 минут\n" \
        "Админ конфы может удалять подписки в конф\n" \
        "Для вк нужно перейти в 'Показать все' и скопировать ссылку оттуда. Также поддерживаются ссылки на плейлисты"

    args = 1
    platforms = [Platform.TG]
    access = Role.TRUSTED

    bot: TgBot

    def start(self) -> ResponseMessage:
        arg0 = self.event.message.args[0]
        menu = [
            [['добавить', 'подписаться', 'подписка'], self.menu_add],
            [['удалить', 'отписаться', 'отписка'], self.menu_delete],
            [['все', 'всё'], self.menu_subs],
            [['конфа'], self.menu_conference],
        ]
        method = self.handle_menu(menu, arg0)
        rmi = method()
        return ResponseMessage(rmi)

    def menu_add(self) -> ResponseMessageItem:
        self.check_args(2)
        self.attachments = [LinkAttachment]
        self.check_attachments()
        attachment: LinkAttachment = self.event.attachments[0]

        # ToDo: сделать красиво
        if attachment.is_youtube_link:
            channel_id, title, date, last_video_id, is_stream, playlist_id = self.menu_add_youtube(attachment.url)
            service = SubscribeModel.SERVICE_YOUTUBE
        elif attachment.is_the_hole_link:
            channel_id, title, date, last_video_id, is_stream, playlist_id = self.menu_add_the_hole(attachment.url)
            service = SubscribeModel.SERVICE_THE_HOLE
        elif attachment.is_wasd_link:
            channel_id, title, date, last_video_id, is_stream, playlist_id = self.menu_add_wasd(attachment.url)
            service = SubscribeModel.SERVICE_WASD
        elif attachment.is_vk_link:
            channel_id, title, date, last_video_id, is_stream, playlist_id = self.menu_add_vk(attachment.url)
            service = SubscribeModel.SERVICE_VK
        else:
            raise PWarning("Незнакомый сервис. Доступные: \nYouTube, The-Hole, WAST, VK")

        if self.event.chat:
            existed_sub = SubscribeModel.objects.filter(chat=self.event.chat, channel_id=channel_id,
                                                        playlist_id=playlist_id)
        else:
            existed_sub = SubscribeModel.objects.filter(chat__isnull=True, channel_id=channel_id,
                                                        playlist_id=playlist_id)
        if existed_sub.exists():
            raise PWarning(f"Ты уже и так подписан на канал {existed_sub.first().title}")

        sub = SubscribeModel(
            author=self.event.user,
            chat=self.event.chat,
            channel_id=channel_id,
            playlist_id=playlist_id,
            title=title,
            date=date,
            service=service,
            last_video_id=last_video_id,
            is_stream=is_stream,
            message_thread_id=self.event.message_thread_id
        )
        sub.save()
        answer = f'Подписал на канал {title}'
        return ResponseMessageItem(text=answer)

    @staticmethod
    def menu_add_youtube(url):
        r = requests.get(url)
        bs4 = BeautifulSoup(r.content, 'html.parser')
        channel_id = bs4.find_all('link', {'rel': 'canonical'})[0].attrs['href'].split('/')[-1]

        youtube_info = YoutubeVideoAPI()
        youtube_data = youtube_info.get_last_video(channel_id)

        title = youtube_data['title']
        date = youtube_data['last_video']['date']
        last_video_id = youtube_data['last_video']['id']
        is_stream = False

        return channel_id, title, date, last_video_id, is_stream, None

    @staticmethod
    def menu_add_the_hole(url):
        the_hole_api = TheHoleAPI()
        parsed = the_hole_api.parse_channel(url)
        is_stream = False

        return parsed['channel_id'], parsed['title'], None, parsed['last_video_id'], is_stream, None

    @staticmethod
    def menu_add_wasd(url):
        wasd_api = WASDAPI()
        parsed = wasd_api.parse_channel(url)
        is_stream = True

        return parsed['channel_id'], parsed['title'], None, None, is_stream, None

    @staticmethod
    def menu_add_vk(url):
        vk_api = VKVideoAPI()
        parsed = vk_api.parse_channel(url)
        is_stream = False

        return parsed['channel_id'], parsed['title'], None, parsed['last_video_id'], is_stream, parsed['playlist_id']

    def menu_delete(self) -> ResponseMessageItem:
        self.check_args(2)
        channel_filter = self.event.message.args[1:]
        sub = self.get_sub(channel_filter, True)
        sub_title = sub.title
        sub.delete()
        answer = f"Удалил подписку на канал {sub_title}"
        return ResponseMessageItem(text=answer)

    def menu_subs(self) -> ResponseMessageItem:
        answer = self.get_subs()
        return ResponseMessageItem(text=answer)

    def menu_conference(self) -> ResponseMessageItem:
        self.check_conversation()
        answer = self.get_subs(conversation=True)
        return ResponseMessageItem(text=answer)

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
