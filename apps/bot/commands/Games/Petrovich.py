import datetime
from threading import Lock

from django.contrib.auth.models import Group
from django.db.models import Min

from apps.bot.classes.Consts import Platform, Role
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import localize_datetime, remove_tz
from apps.games.models import PetrovichGames, PetrovichUser
from petrovich.settings import DEFAULT_TIME_ZONE

lock = Lock()


class Petrovich(CommonCommand):
    names = ["петрович", 'петровна']
    help_text = "Петрович - мини-игра, определяющая кто Петрович Дня"
    detail_help_text = "Петрович - мини-игра, определяющая кто Петрович дня\n" \
                       "Петрович рег - регистрация в игре\n" \
                       "Петрович дерег - дерегистрация в игре"
    conversation = True
    platforms = [Platform.VK, Platform.TG]

    def start(self):
        if self.event.args:
            arg0 = self.event.args[0].lower()
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
        p_user = PetrovichUser.objects.filter(user=self.event.sender, chat=self.event.chat).first()
        if p_user is not None:
            if not p_user.active:
                p_user.active = True
                p_user.save()
                return "Возвращаю тебя в строй"
            else:
                return "Ты уже зарегистрирован :)"
        min_wins = PetrovichUser.objects.filter(chat=self.event.chat).aggregate(Min('wins'))['wins__min']

        p_user = PetrovichUser(user=self.event.sender,
                               chat=self.event.chat,
                               active=True)

        if min_wins:
            p_user.wins = min_wins
        p_user.save()

        return "Регистрация прошла успешно"

    def menu_dereg(self):
        p_user = PetrovichUser.objects.filter(user=self.event.sender, chat=self.event.chat).first()
        if p_user is not None and p_user.active:
            p_user.active = False
            p_user.save()
            return "Ок"
        else:
            return "А ты и не зареган"

    def menu_play(self):
        with lock:
            winner_today = PetrovichGames.objects.filter(chat=self.event.chat).last()
            if winner_today:
                datetime_now = localize_datetime(datetime.datetime.utcnow(), DEFAULT_TIME_ZONE)
                datetime_last = localize_datetime(remove_tz(winner_today.date), DEFAULT_TIME_ZONE)
                if (datetime_now.date() - datetime_last.date()).days <= 0:
                    if winner_today.user.gender and winner_today.user.gender == '1':
                        winner_gender = "Петровна"
                    else:
                        winner_gender = "Петрович"
                    return f"{winner_gender} дня - {winner_today.user}"
            group_banned = Group.objects.get(name=Role.BANNED.name)
            winner = PetrovichUser.objects.filter(chat=self.event.chat, active=True).exclude(
                user__groups=group_banned).order_by("?").first()
            if winner:
                winner = winner.user
            else:
                raise PWarning("Нет участников игры. Зарегистрируйтесь! /петрович рег")

            PetrovichGames.objects.filter(chat=self.event.chat).delete()
            PetrovichGames(user=winner, chat=self.event.chat).save()
            winner_petrovich = PetrovichUser.objects.filter(user=winner, chat=self.event.chat).first()
            winner_petrovich.wins += 1
            winner_petrovich.save()
            if winner_petrovich.user.gender and winner_petrovich.user.gender == '1':
                winner_gender = "Наша сегодняшняя Петровна дня"
            else:
                winner_gender = "Наш сегодняшний Петрович дня"
            messages = ["Такс такс такс, кто тут у нас",
                        f"{winner_gender} - {self.bot.get_mention(winner_petrovich.user, str(winner_petrovich.user))}"]
            return messages
