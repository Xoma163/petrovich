import datetime

from django.db.models import Count

from apps.bot.classes.Command import Command
from apps.bot.models import Profile
from apps.games.models import Gamer
from apps.games.models import PetrovichUser
from apps.service.models import Meme


class Statistics(Command):
    name = "статистика"
    names = ["стата"]
    help_text = "статистика по победителям игр или по кол-ву созданных мемов"
    help_texts = [
        "[модуль=все] - статистика по победителям игр или по кол-ву созданных мемов.\nМодули: петрович, ставки, рулетка, мемы",
        "(петрович) [год=текущий] - статистика по победителям петровича."
    ]
    conversation = True

    def start(self):
        if not self.event.message.args:
            return self.menu_all()
        else:
            arg0 = self.event.message.args[0]
            menu = [
                [['петрович'], self.menu_petrovich],
                [['ставки'], self.menu_rates],
                [['рулетка'], self.menu_roulettes],
                [['мемы'], self.menu_memes]
            ]
            method = self.handle_menu(menu, arg0)
            return method()

    def menu_petrovich(self):
        if len(self.event.message.args) > 1:
            self.int_args = [1]
            self.parse_int()
            year = self.event.message.args[1]
        else:
            year = datetime.datetime.now().year

        players = PetrovichUser.objects \
            .filter(chat=self.event.chat) \
            .filter(profile__chats=self.event.chat)
        players = sorted(players, key=lambda t: t.wins_by_year(year), reverse=True)

        players_list = [player for player in players if player.wins_by_year(year)]
        msg = "Наши любимые Петровичи:\n"
        if len(players_list) == 0:
            return msg + f"Нет статистики за {year} год"

        players_list_str = "\n".join([f"{player} - {player.wins_by_year(year)}" for player in players_list])
        return msg + players_list_str

    def menu_rates(self):
        gamers = Gamer.objects.filter(profile__chats=self.event.chat).exclude(points=0).order_by('-points')
        msg = "Победители ставок:\n"
        if gamers.count() == 0:
            raise RuntimeWarning(msg + "Нет статистики")
        gamers_str = "\n".join([f"{gamer} - {gamer.points}" for gamer in gamers])
        return msg + gamers_str

    def menu_roulettes(self):
        gamers = Gamer.objects.filter(profile__chats=self.event.chat).exclude(roulette_points=0).order_by(
            '-roulette_points')
        msg = "Очки рулетки:\n"
        if gamers.count() == 0:
            raise RuntimeWarning(msg + "Нет статистики")
        gamers_str = "\n".join([f"{gamer} - {gamer.roulette_points}" for gamer in gamers])
        return msg + gamers_str

    def menu_memes(self):
        profiles = Profile.objects.filter(chats=self.event.chat)

        result_list = list(
            Meme.objects.filter(author__in=profiles).values('author').annotate(total=Count('author')).order_by(
                '-total'))
        msg = "Созданных мемов:\n"
        if len(result_list) == 0:
            raise RuntimeWarning(msg + "Нет статистики")
        result_list_str = "\n".join([f"{profiles.get(id=x['author'])} - {x['total']}" for x in result_list])
        return msg + result_list_str

    def menu_all(self):

        methods = [
            self.menu_petrovich,
            self.menu_rates,
            self.menu_roulettes,
            self.menu_memes
        ]
        msg = ""
        for val in methods:
            msg += f"{val()}\n\n"
        return msg
