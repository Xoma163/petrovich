from django.db.models import Count

from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.games.models import Gamer
from apps.games.models import PetrovichUser
from apps.service.models import Meme


class Statistics(CommonCommand):
    name = "статистика"
    names = ["стата"]
    help_text = "статистика по победителям игр или по кол-ву созданных мемов"
    help_texts = [
        "[модуль=все] - статистика по победителям игр или по кол-ву созданных мемов.\n"
        "Модули: петрович, ставки, рулетка, мемы"
    ]
    conversation = True

    def start(self):
        if not self.event.message.args:
            return self.menu_all()
        else:
            arg0 = self.event.message.args[0].lower()
            menu = [
                [['петрович'], self.menu_petrovich],
                [['ставки'], self.menu_rates],
                [['рулетка'], self.menu_roulettes],
                [['мемы'], self.menu_memes]
            ]
            method = self.handle_menu(menu, arg0)
            return method()

    def menu_petrovich(self):
        players = PetrovichUser.objects \
            .filter(chat=self.event.chat) \
            .filter(user__chats=self.event.chat) \
            .order_by('-wins')
        msg = "Наши любимые Петровичи:\n"
        for player in players:
            msg += "%s - %s\n" % (player, player.wins)
        return msg

    def menu_rates(self):
        gamers = Gamer.objects.filter(user__chats=self.event.chat).exclude(points=0).order_by('-points')
        msg = "Победители ставок:\n"
        for gamer in gamers:
            msg += f"{gamer} - {gamer.points}\n"
        return msg

    def menu_roulettes(self):
        gamers = Gamer.objects.filter(user__chats=self.event.chat).exclude(roulette_points=0).order_by(
            '-roulette_points')
        msg = "Очки рулетки:\n"
        for gamer in gamers:
            msg += f"{gamer} - {gamer.roulette_points}\n"
        return msg

    def menu_memes(self):
        users = self.bot.user_model.filter(chats=self.event.chat)

        result_list = list(
            Meme.objects.filter(author__in=users).values('author').annotate(total=Count('author')).order_by('-total'))
        msg = "Созданных мемов:\n"
        for result in result_list:
            msg += f"{users.get(id=result['author'])} - {result['total']}\n"
        return msg

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
