from django.db.models import Count

from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.games.models import Gamer
from apps.games.models import PetrovichUser
from apps.service.models import Meme


# ToDo: TG
class Statistics(CommonCommand):
    def __init__(self):
        names = ["стата", "статистика"]
        help_text = "Стата - статистика по победителям игр или по кол-ву созданных мемов"
        detail_help_text = "Стата [модуль=все] - статистика по победителям игр или по кол-ву созданных мемов. Модули:\n" \
                           "петрович, ставки, крестики, рулетка, коднеймс, мемы"
        super().__init__(names, help_text, detail_help_text, conversation=True, enabled=False)

    def start(self):
        if not self.event.args:
            return self.menu_all()
        else:
            arg0 = self.event.args[0].lower()
            menu = [
                [['петрович'], self.menu_petrovich],
                [['ставки'], self.menu_rates],
                [['крестики'], self.menu_tic_tac_toe],
                [['коднеймс'], self.menu_codenames],
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

    def menu_tic_tac_toe(self):
        gamers = Gamer.objects.filter(user__chats=self.event.chat).exclude(tic_tac_toe_points=0).order_by(
            '-tic_tac_toe_points')
        msg = "Победители крестиков-ноликов:\n"
        for gamer in gamers:
            msg += f"{gamer} - {gamer.tic_tac_toe_points}\n"
        return msg

    def menu_codenames(self):
        gamers = Gamer.objects.filter(user__chats=self.event.chat).exclude(codenames_points=0).order_by(
            '-codenames_points')
        msg = "Победители коднеймса:\n"
        for gamer in gamers:
            msg += f"{gamer} - {gamer.codenames_points}\n"
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
            self.menu_tic_tac_toe,
            self.menu_codenames,
            self.menu_roulettes,
            self.menu_memes
        ]
        msg = ""
        for val in methods:
            msg += f"{val()}\n\n"
        return msg
