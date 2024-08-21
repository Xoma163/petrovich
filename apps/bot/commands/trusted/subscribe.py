from django.db.models import Q

from apps.bot.api.media.vk.video import VKVideo
from apps.bot.api.media.youtube.video import YoutubeVideo
from apps.bot.api.subscribe_service import SubscribeServiceData
from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role, Platform
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextItem, HelpText, HelpTextArgument
from apps.bot.classes.messages.attachments.link import LinkAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.service.models import Subscribe as SubscribeModel

MAX_USER_SUBS_COUNT = 3


class Subscribe(Command):
    name = "подписка"
    names = ['подписки']

    help_text = HelpText(
        commands_text="создаёт подписку на каналы. Доступные: YouTube, VK Видео. Бот пришлёт тебе новое видео с канала когда оно выйдет",
        help_texts=[
            HelpTextItem(Role.TRUSTED, [
                HelpTextArgument(None, "список активных подписок в лс, если в конфе, то только общие в конфе"),
                HelpTextArgument("добавить (ссылка на канал/плейлист)", "создаёт подписку на канал."),
                HelpTextArgument("удалить (название канала/плейлиста/id)", "удаляет вашу подписку на канал"),
            ])
        ],
        extra_text=(
            "Проверка новых видео проходит каждые 30 минут\n"
            "Для вк нужно перейти в 'Показать все' и скопировать ссылку оттуда. Также поддерживаются ссылки на плейлисты для VK/Youtube"
        ),
    )

    platforms = [Platform.TG]
    access = Role.TRUSTED

    bot: TgBot

    def start(self) -> ResponseMessage:
        arg0 = self.event.message.args[0] if self.event.message.args else None
        menu = [
            [['добавить', 'подписаться', 'подписка'], self.menu_add],
            [['удалить', 'отписаться', 'отписка'], self.menu_delete],
            [['default'], self.menu_subs],
        ]
        method = self.handle_menu(menu, arg0)
        rmi = method()
        return ResponseMessage(rmi)

    def menu_add(self) -> ResponseMessageItem:
        self.check_args(2)
        self.attachments = [LinkAttachment]
        self.check_attachments()
        attachment: LinkAttachment = self.event.attachments[0]

        if attachment.is_youtube_link:
            data = self.add_youtube(attachment.url)
        elif attachment.is_vk_link:
            data = self.add_vk(attachment.url)
        else:
            raise PWarning("Незнакомый сервис. Доступные: \nYouTube, VK video")

        if self.event.chat:
            existed_sub = SubscribeModel.objects.filter(
                chat=self.event.chat,
                channel_id=data.channel_id,
                playlist_id=data.playlist_id
            )
        else:
            existed_sub = SubscribeModel.objects.filter(
                chat__isnull=True,
                author=self.event.user,
                channel_id=data.channel_id,
                playlist_id=data.playlist_id
            )
        if existed_sub.exists():
            if data.playlist_id:
                raise PWarning(
                    f"Ты уже и так подписан на плейлист \"{existed_sub.first().playlist_title}\" канала \"{existed_sub.first().channel_title}\"")
            raise PWarning(f"Ты уже и так подписан на канал \"{existed_sub.first().channel_title}\"")

        data_dict = data.__dict__

        data_dict.update({
            "author": self.event.user,
            "chat": self.event.chat,
            "message_thread_id": self.event.message_thread_id,
        })

        sub = SubscribeModel(**data_dict)
        sub.save()
        if sub.playlist_id:
            answer = f"Подписал на плейлист \"{data.playlist_title}\" канала \"{data.channel_title}\""
        else:
            answer = f"Подписал на канал \"{data.channel_title}\""
        return ResponseMessageItem(text=answer)

    @staticmethod
    def add_youtube(url) -> SubscribeServiceData:
        yt_api = YoutubeVideo()
        parsed = yt_api.get_channel_info(url)
        parsed.service = SubscribeModel.SERVICE_YOUTUBE
        return parsed

    @staticmethod
    def add_vk(url) -> SubscribeServiceData:
        vk_api = VKVideo()
        parsed = vk_api.get_channel_info(url)
        parsed.service = SubscribeModel.SERVICE_VK
        return parsed

    def menu_subs(self) -> ResponseMessageItem:
        subs = self.get_filtered_subs()
        rmi = ResponseMessageItem(text=self.get_subs_str(subs))
        return rmi

    def menu_delete(self) -> ResponseMessageItem:
        self.check_args(2)
        channel_filter = self.event.message.args[1:]
        sub = self.get_sub(channel_filter)
        sub_title = sub.channel_title
        playlist_title = sub.playlist_title
        sub.delete()
        if playlist_title:
            answer = f"Удалил подписку на плейлист \"{playlist_title}\" канала \"{sub_title}\""
        else:
            answer = f"Удалил подписку на канал \"{sub_title}\""
        return ResponseMessageItem(text=answer)

    def get_sub(self, filters) -> SubscribeModel:
        filters = [x for x in filters if x != "|"]
        subs = self.get_filtered_subs()
        try:
            pk = int(filters[0])
            subs = subs.filter(pk=pk)
        except ValueError:
            for _filter in filters:
                q = Q(channel_title__icontains=_filter) | Q(playlist_title__icontains=_filter)
                subs = subs.filter(q)

        subs_count = subs.count()
        if subs_count == 0:
            raise PWarning("Не нашёл :(")
        elif subs_count > 1:
            msg = f"Нашёл сразу {subs_count}. уточните:\n\n" \
                  f"{self.get_subs_str(subs)}"
            raise PWarning(msg)

        return subs.first()

    def get_subs_str(self, subs) -> str:
        subs_titles_str = ""
        for sub in subs:
            if sub.playlist_title:
                title = f"{sub.channel_title} | {sub.playlist_title}"
            else:
                title = sub.channel_title
            subs_titles_str += f"[{sub.get_service_display()} id:{self.bot.get_formatted_text_line(sub.pk)}] {self.bot.get_formatted_text_line(title)}"
            if sub.chat:
                subs_titles_str += f" (конфа - {sub.chat})"
            subs_titles_str += '\n'
        return subs_titles_str

    def get_filtered_subs(self) -> SubscribeModel.objects:
        if self.event.chat:
            subs = SubscribeModel.objects.filter(chat=self.event.chat)
        else:
            subs = SubscribeModel.objects.filter(author=self.event.user)
        if subs.count() == 0:
            raise PWarning("Нет активных подписок")
        return subs
