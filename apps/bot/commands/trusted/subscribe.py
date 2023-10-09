from apps.bot.api.premier import Premier
from apps.bot.api.thehole import TheHole
from apps.bot.api.vk.video import VKVideo
from apps.bot.api.youtube.video import YoutubeVideo
from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role, Platform
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.attachments.link import LinkAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.service.models import Subscribe as SubscribeModel

MAX_USER_SUBS_COUNT = 3


class Subscribe(Command):
    name = "подписка"
    names = ['подписки']
    help_text = "создаёт подписку на каналы. Доступные: YouTube, The-Hole, WAST, VK, Premier"
    help_texts = [
        "добавить (ссылка на канал) - создаёт подписку на канал. Бот пришлёт тебе новое видео с канала",
        "удалить (название канала) - удаляет вашу подписку на канал (если в конфе, то только по конфе, в лс только по лс)",
        "все - пришлёт активные подписки",
        "конфа - пришлёт активные подписки по конфе"
    ]
    help_texts_extra = (
        "Проверка новых видео проходит каждые 10 минут. Стримов - 5 минут\n"
        "Админ конфы может удалять подписки в конф\n"
        "Для вк нужно перейти в 'Показать все' и скопировать ссылку оттуда. Также поддерживаются ссылки на плейлисты"
    )

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
            data = self.add_youtube(attachment.url)
        elif attachment.is_the_hole_link:
            data = self.add_the_hole(attachment.url)
        elif attachment.is_vk_link:
            data = self.add_vk(attachment.url)
        elif attachment.is_premier_link:
            data = self.add_premiere(attachment.url)
        else:
            raise PWarning("Незнакомый сервис. Доступные: \nYouTube, The-Hole, VK, Premier")

        if self.event.chat:
            existed_sub = SubscribeModel.objects.filter(
                chat=self.event.chat,
                channel_id=data["channel_id"],
                playlist_id=data["playlist_id"]
            )
        else:
            existed_sub = SubscribeModel.objects.filter(
                chat__isnull=True,
                author=self.event.user,
                channel_id=data["channel_id"],
                playlist_id=data["playlist_id"]
            )
        if existed_sub.exists():
            raise PWarning(f"Ты уже и так подписан на канал {existed_sub.first().title}")

        data.update({
            "author": self.event.user,
            "chat": self.event.chat,
            "message_thread_id": self.event.message_thread_id,
        })

        sub = SubscribeModel(**data)
        sub.save()
        answer = f'Подписал на канал {data["title"]}'
        return ResponseMessageItem(text=answer)

    @staticmethod
    def add_youtube(url):
        yt_api = YoutubeVideo()
        parsed = yt_api.get_data_to_add_new_subscribe(url)
        parsed['service'] = SubscribeModel.SERVICE_YOUTUBE
        return parsed

    @staticmethod
    def add_the_hole(url):
        the_hole_api = TheHole()
        parsed = the_hole_api.get_data_to_add_new_subscribe(url)
        parsed['service'] = SubscribeModel.SERVICE_THE_HOLE
        return parsed

    @staticmethod
    def add_vk(url):
        vk_api = VKVideo()
        parsed = vk_api.get_data_to_add_new_subscribe(url)
        parsed['service'] = SubscribeModel.SERVICE_VK
        return parsed

    @staticmethod
    def add_premiere(url):
        p_api = Premier()
        parsed = p_api.get_data_to_add_new_subscribe(url)
        parsed['service'] = SubscribeModel.SERVICE_PREMIERE
        if not parsed:
            raise PWarning("Необходима ссылка на сериал, не фильм")
        return parsed

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
