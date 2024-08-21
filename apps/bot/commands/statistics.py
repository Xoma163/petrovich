import datetime

from django.db.models import Count

from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextArgument, HelpTextItem, HelpTextKey
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.models import Profile
from apps.games.models import PetrovichUser
from apps.service.models import Meme


class Statistics(Command):
    name = "статистика"
    names = ["стата"]

    help_text = HelpText(
        commands_text="статистика по победителям игр или по кол-ву созданных мемов",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextArgument("[модуль=все]", "статистика по победителям-петровичам и по кол-ву созданных мемов"),
                HelpTextArgument("(петрович) [год=текущий]", "статистика по победителям петровича")
            ])
        ],
        help_text_keys=[
            HelpTextItem(Role.USER, [
                HelpTextKey("all", None,
                            "если выбран модуль петрович, то выведутся пользователя которые также покинули группу")
            ])
        ],
        extra_text=(
            "Модули: петрович, мемы, \n"
            "Если выбран модуль петрович и передан ключ --all, то выведутся пользователи которые также покинули группу"
        ),
    )

    def start(self) -> ResponseMessage:
        if not self.event.message.args:
            answer = self.menu_all()
        else:
            arg0 = self.event.message.args[0]
            menu = [
                [['петрович'], self.menu_petrovich],
                [['мемы'], self.menu_memes],
            ]
            method = self.handle_menu(menu, arg0)
            answer = method()
        return ResponseMessage(ResponseMessageItem(text=answer))

    def menu_petrovich(self) -> str:
        self.check_conversation()

        if len(self.event.message.args) > 1:
            self.int_args = [1]
            self.parse_int()
            year = self.event.message.args[1]
        else:
            year = datetime.datetime.now().year

        keys_to_check = {"all", "все"}
        if self.event.message.keys and keys_to_check.intersection(self.event.message.keys):
            players = PetrovichUser.objects.filter(chat=self.event.chat)
        else:
            players = PetrovichUser.objects.filter(chat=self.event.chat, profile__chats=self.event.chat)

        players = sorted(players, key=lambda t: t.wins_by_year(year), reverse=True)

        players_list = [player for player in players if player.wins_by_year(year)]
        msg = "Наши любимые Петровичи:\n"
        if len(players_list) == 0:
            return msg + f"Нет статистики за {year} год"

        players_list_str = "\n".join([f"{player} - {player.wins_by_year(year)}" for player in players_list])
        return msg + players_list_str

    def menu_memes(self) -> str:
        if self.event.is_from_chat:
            profiles = Profile.objects.filter(chats=self.event.chat)
        else:
            profiles = Profile.objects.filter(pk=self.event.sender.pk)

        result_list = Meme.objects.filter(author__in=profiles) \
            .values('author') \
            .annotate(total=Count('author')) \
            .order_by('-total')

        msg = "Созданных мемов:"
        if self.event.is_from_pm:
            return f"{msg} {result_list[0]['total']}"

        if result_list.count() == 0:
            raise PWarning(f"{msg}\nНет статистики")
        result_list_str = "\n".join([f"{profiles.get(id=x['author'])} - {x['total']}" for x in result_list])
        return f"{msg}\n{result_list_str}"

    def menu_all(self):
        methods = [
            self.menu_petrovich,
            self.menu_memes,
        ]
        answer = ""
        for val in methods:
            try:
                answer += f"{val()}\n\n"
            except PWarning:
                continue
        return answer
