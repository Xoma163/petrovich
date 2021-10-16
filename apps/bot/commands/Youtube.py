import requests
from bs4 import BeautifulSoup

from apps.bot.APIs.YoutubeInfo import YoutubeInfo
from apps.bot.classes.Consts import Role, Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.service.models import YoutubeSubscribe

MAX_USER_SUBS_COUNT = 3


class YouTube(CommonCommand):
    name = "ютуб"
    help_text = "создаёт подписку на ютуб канал"
    help_texts = [
        "добавить (ссылка на канал) - создаёт подписку на канал. Бот пришлёт тебе новое видео с канала",
        f"удалить (название канала) - удаляет вашу подписку на канал (если в конфе, то только по конфе, в лс только по лс). Максимум подписок - {MAX_USER_SUBS_COUNT} шт. Админ конфы может удалять подписки в конфе",
        "подписки - пришлёт ваши активные подписки (если в конфе, то только подписки по конфе)",
        "конфа - пришлёт активные подписки по конфе\n",

        # "Чтобы узнать id канала нужно перейти на канал и скопировать содержимое после https://www.youtube.com/channel/{id}\n",
        # "Чтобы узнать название канала, нужно перейти на канал и скопировать содержимое после https://www.youtube.com/user/{name} или https://www.youtube.com/{name}\n",
        "Проверка новых видео проходит каждый час"
    ]
    args = 1
    platforms = [Platform.VK, Platform.TG]

    def start(self):
        arg0 = self.event.message.args[0].lower()
        menu = [
            [['добавить', 'подписаться', 'подписка'], self.menu_add],
            [['удалить', 'отписаться', 'отписка'], self.menu_delete],
            [['подписки'], self.menu_subs],
            [['конфа'], self.menu_conference],
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    def menu_add(self):
        self.check_args(2)
        channel_url = self.event.message.args[1]
        try:
            response = requests.get(channel_url)
            bsop = BeautifulSoup(response.content, 'html.parser')
            channel_id = bsop.find_all('link', {'rel': 'canonical'})[0].attrs['href'].split('/')[-1]
        except:
            return PWarning("Некорректная ссылка на ютуб канал")

        if self.event.chat:
            existed_sub = YoutubeSubscribe.objects.filter(chat=self.event.chat,
                                                          channel_id=channel_id)
        else:
            existed_sub = YoutubeSubscribe.objects.filter(chat__isnull=True,
                                                          channel_id=channel_id)
        if existed_sub.exists():
            raise PWarning(f"Ты уже и так подписан на канал {existed_sub.first().title}")

        user_subs_count = YoutubeSubscribe.objects.filter(author=self.event.sender).count()

        # Ограничение 3 подписки для нетрастед
        if not self.event.sender.check_role(Role.TRUSTED) and user_subs_count >= MAX_USER_SUBS_COUNT:
            return f"Максимальное число подписок - {MAX_USER_SUBS_COUNT}"
        youtube_info = YoutubeInfo(channel_id)
        youtube_data = youtube_info.get_youtube_channel_info()
        yt_sub = YoutubeSubscribe(
            author=self.event.sender,
            chat=self.event.chat,
            channel_id=channel_id,
            title=youtube_data['title'],
            date=youtube_data['last_video']['date']
        )
        yt_sub.save()
        return f'Подписал на канал {youtube_data["title"]}'

    def menu_delete(self):
        self.check_args(2)
        channel_filter = self.event.message.args[1:]
        yt_sub = self.get_sub(channel_filter, True)
        yt_sub_title = yt_sub.title
        yt_sub.delete()
        return f"Удалил подписку на канал {yt_sub_title}"

    def menu_subs(self):
        return self.get_subs()

    def menu_conference(self):
        self.check_conversation()
        return self.get_subs(conversation=True)

    def get_sub(self, filters, for_delete=False):
        if self.event.chat:
            yt_subs = YoutubeSubscribe.objects.filter(chat=self.event.chat)
            if self.event.chat.admin != self.event.sender:
                yt_subs = yt_subs.filter(author=self.event.sender)
        else:
            yt_subs = YoutubeSubscribe.objects.filter(author=self.event.sender)
            if for_delete:
                yt_subs = yt_subs.filter(chat__isnull=True)

        for _filter in filters:
            yt_subs = yt_subs.filter(title__icontains=_filter)

        yt_subs_count = yt_subs.count()
        if yt_subs_count == 0:
            raise PWarning("Не нашёл :(")
        elif yt_subs_count == 1:
            return yt_subs.first()
        else:
            filters_str = " ".join(filters)
            for yt_sub in yt_subs:
                if yt_sub.title == filters_str:
                    return yt_sub
            yt_subs = yt_subs[:10]
            yt_subs_titles = [yt_sub.title for yt_sub in yt_subs]
            yt_subs_titles_str = ";\n".join(yt_subs_titles)

            msg = f"Нашёл сразу {yt_subs_count}. уточните:\n\n" \
                  f"{yt_subs_titles_str}" + '.'
            if yt_subs_count > 10:
                msg += "\n..."
            raise PWarning(msg)

    def get_subs(self, conversation=False):
        if conversation:
            yt_subs = YoutubeSubscribe.objects.filter(chat=self.event.chat)
        else:
            yt_subs = YoutubeSubscribe.objects.filter(author=self.event.sender)
            if self.event.chat:
                yt_subs = yt_subs.filter(chat=self.event.chat)
        if yt_subs.count() == 0:
            raise PWarning("Нет активных подписок")

        yt_subs_titles_str = ""
        for yt_sub in yt_subs:
            yt_subs_titles_str += yt_sub.title
            if not conversation and yt_sub.chat:
                yt_subs_titles_str += f" (конфа - {yt_sub.chat})"
            yt_subs_titles_str += '\n'

        return yt_subs_titles_str
