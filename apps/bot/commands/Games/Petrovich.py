import datetime
from threading import Lock

from django.contrib.auth.models import Group

from apps.bot.classes.Command import Command
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.consts.Consts import Platform, Role
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.utils import localize_datetime, remove_tz, random_event
from apps.games.models import PetrovichGames, PetrovichUser
from petrovich.settings import DEFAULT_TIME_ZONE

lock = Lock()


class Petrovich(Command):
    name = "петрович"
    names = ['петровна']
    name_tg = 'petrovich'

    help_text = "мини-игра, определяющая кто Петрович Дня"
    help_texts = [
        "- мини-игра, определяющая кто Петрович дня",
        "рег - регистрация в игре",
        "дерег - дерегистрация в игре"
    ]

    conversation = True
    platforms = [Platform.TG]
    access = Role.GAMER

    bot: TgBot

    def start(self):
        if self.event.message.args:
            arg0 = self.event.message.args[0]
        else:
            arg0 = None
        menu = [
            [['рег', 'регистрация'], self.menu_reg],
            [['дерег'], self.menu_dereg],
            [['default'], self.menu_play]
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    def menu_reg(self):
        p_user = PetrovichUser.objects.filter(profile=self.event.sender, chat=self.event.chat).first()
        if p_user is not None:
            if not p_user.active:
                p_user.active = True
                p_user.save()
                return "Возвращаю тебя в строй"
            else:
                return "Ты уже зарегистрирован"

        PetrovichUser.objects.create(profile=self.event.sender, chat=self.event.chat, active=True)
        return "Регистрация прошла успешно"

    def menu_dereg(self):
        p_user = PetrovichUser.objects.filter(profile=self.event.sender, chat=self.event.chat).first()
        if p_user is not None and p_user.active:
            p_user.active = False
            p_user.save()
            return "Ок"
        else:
            return "А ты и не зареган"

    def menu_play(self):
        with lock:
            datetime_now = localize_datetime(datetime.datetime.utcnow(), DEFAULT_TIME_ZONE)
            winner_today = PetrovichGames.objects.filter(chat=self.event.chat).first()
            if winner_today:
                datetime_last = localize_datetime(remove_tz(winner_today.date), DEFAULT_TIME_ZONE)
                if (datetime_now.date() - datetime_last.date()).days <= 0:
                    if winner_today.profile.gender and winner_today.profile.gender == '1':
                        winner_gender = "Петровна"
                    else:
                        winner_gender = "Петрович"
                    return f"{winner_gender} дня - {winner_today.profile}"

            group_banned = Group.objects.get(name=Role.BANNED.name)
            winner = PetrovichUser.objects \
                .filter(chat=self.event.chat, active=True) \
                .exclude(profile__groups=group_banned) \
                .filter(profile__chats=self.event.chat) \
                .order_by("?") \
                .first()
            if winner:
                winner = winner.profile
            else:
                button = self.bot.get_button('Зарегистрироваться', self.name, 'рег')
                keyboard = self.bot.get_inline_keyboard([button])
                raise PWarning(
                    f"Нет участников игры. Зарегистрируйтесь! {self.bot.get_formatted_text_line('/петрович рег')}",
                    keyboard=keyboard
                )

            winner_petrovich = PetrovichGames(profile=winner, chat=self.event.chat)
            winner_petrovich.save()
            if winner.gender and winner.gender == '1':
                winner_gender = "Наша сегодняшняя Петровна дня"
            else:
                winner_gender = "Наш сегодняшний Петрович дня"

            first_message = random_event(
                [
                    "Такс такс такс, кто тут у нас",
                    "*барабанная дробь*",
                    "Вы готовы узнать победителя голодных игр?",
                    "Ну шо, погнали",
                    "Вы не поверите...",
                    "Опять вы в игрульки свои играете да? Ну ладно"
                ]
            )

            return [
                first_message,
                f"{winner_gender} - {self.bot.get_mention(winner, str(winner))}"
            ]
