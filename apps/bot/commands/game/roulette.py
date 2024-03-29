import datetime
from threading import Lock

from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextItem, HelpText, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import random_event, localize_datetime, remove_tz, decl_of_num, \
    get_random_int
from apps.games.models import RouletteRate, Gamer
# Кратно 12
from petrovich.settings import DEFAULT_TIME_ZONE, STATIC_ROOT

MAX_NUMBERS = 36

lock = Lock()


def generate_translator():
    # By E.Dubovitsky
    def is_red(n):
        j = (n - 1) % 9  # номер в квадратике
        i = (n - 1) / 9  # номер самого квадратика

        j_even = j % 2 == 0  # попадает ли номер внутри квадратика в крестик
        i_even = i % 2 == 0  # чётный ли сам квадратик

        return j_even and (i_even or j != 0)

    translator_numbers = {
        str(i): {
            'win_numbers': [i],
            'coefficient': MAX_NUMBERS,
            'verbose_name': i
        } for i in range(MAX_NUMBERS + 1)
    }
    translator = {
        "красное": {
            "win_numbers": [i for i in range(1, MAX_NUMBERS + 1) if is_red(i)],
            "coefficient": 2,
            "verbose_name": "красное"
        },
        "черное": {
            "win_numbers": [i for i in range(1, MAX_NUMBERS + 1) if not is_red(i)],
            "coefficient": 2,
            "verbose_name": "чёрное"
        },
        "строка": {
            1: {
                "win_numbers": [i for i in range(3, MAX_NUMBERS + 1, 3)],
                "coefficient": 3,
                "verbose_name": "1я строка"
            },
            2: {
                "win_numbers": [i for i in range(2, MAX_NUMBERS, 3)],
                "coefficient": 3,
                "verbose_name": "2 строка"
            },
            3: {
                "win_numbers": [i for i in range(1, MAX_NUMBERS, 3)],
                "coefficient": 3,
                "verbose_name": "3 строка"
            },
        },
        "столбец": {
            1: {
                "win_numbers": [i for i in range(1, MAX_NUMBERS // 3 + 1)],
                "coefficient": 3,
                "verbose_name": "1 столбец"
            },
            2: {
                "win_numbers": [i for i in range(MAX_NUMBERS // 3 + 1, MAX_NUMBERS * 2 // 3 + 1)],
                "coefficient": 3,
                "verbose_name": "2 столбец"
            },
            3: {
                "win_numbers": [i for i in range(MAX_NUMBERS * 2 // 3 + 1, MAX_NUMBERS + 1)],
                "coefficient": 3,
                "verbose_name": "3 столбец"
            },
        },
        "первая": {
            "win_numbers": [i for i in range(1, MAX_NUMBERS // 2 + 1)],
            "coefficient": 2,
            "verbose_name": "первая половина"
        },
        "вторая": {
            "win_numbers": [i for i in range(MAX_NUMBERS // 2 + 1, MAX_NUMBERS + 1)],
            "coefficient": 2,
            "verbose_name": "вторая половина",
        },
        "четное": {
            "win_numbers": [i for i in range(2, MAX_NUMBERS + 1, 2)],
            "coefficient": 2,
            "verbose_name": "чётное"
        },
        "нечетное": {
            "win_numbers": [i for i in range(1, MAX_NUMBERS, 2)],
            "coefficient": 2,
            "verbose_name": "нечётное"
        },
    }

    translator.update(translator_numbers)
    return translator


TRANSLATOR = generate_translator()


class Roulette(Command):
    name = "рулетка"

    help_text = HelpText(
        commands_text="игра рулетка",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand(None, "запуск рулетки"),
                HelpTextItemCommand("(аргументы) (ставка)", "ставка рулетки"),
                HelpTextItemCommand(f"0-{MAX_NUMBERS} (ставка)", "ставка на число"),
                HelpTextItemCommand("столбец (1,2,3) (ставка)", "ставка на столбец"),
                HelpTextItemCommand("строка (1,2,3) (ставка)", "ставка на строку"),
                HelpTextItemCommand("красное/чёрное (ставка)", "ставка на цвет"),
                HelpTextItemCommand("чётное/нечётное (ставка)", "ставка на кратность"),
                HelpTextItemCommand("первая/вторая (ставка)", "ставка на 1/2 части стола"),
                HelpTextItemCommand("баланс [игрок]", "баланс"),
                HelpTextItemCommand("ставки", "текущие ставки игроков"),
                HelpTextItemCommand("картинка", "картинка рулетки"),
                HelpTextItemCommand("бонус", "получение пособия по безработице"),
                HelpTextItemCommand("передать (игрок) (очки)", "передача очков другому игроку")
            ])
        ]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gamer = None

    def start(self) -> ResponseMessage:
        if not self.event.message.args:
            rmi = self.menu_play()
            return ResponseMessage(rmi)
        arg0 = self.event.message.args[0]

        self.gamer = self.event.sender.gamer

        menu = [
            [['баланс'], self.menu_balance],
            [['картинка'], self.menu_picture],
            [['бонус'], self.menu_bonus],
            [['передать', 'перевод', 'перевести', 'подать'], self.menu_transfer],
            [['выдать', 'начислить', 'зачислить'], self.menu_give],
            [['ставки'], self.menu_rates],
            [['default'], self.menu_rate_on]
        ]
        method = self.handle_menu(menu, arg0)
        rmi = method()
        return ResponseMessage(rmi)

    def menu_balance(self) -> ResponseMessageItem:
        if len(self.event.message.args) > 1:
            user = self.bot.get_profile_by_name(self.event.message.args[1:], self.event.chat)
            user_gamer = Gamer.objects.filter(profile=user).first()
            if not user_gamer:
                raise PWarning("Не нашёл такого игрока")
            answer = f"Баланс игрока {user} - {user_gamer.roulette_points}"
            return ResponseMessageItem(text=answer)
        answer = f"Ваш баланс - {self.gamer.roulette_points}"
        return ResponseMessageItem(text=answer)

    def menu_picture(self) -> ResponseMessageItem:
        photo = random_event(
            [f"{STATIC_ROOT}/bot/img/roulette_game.jpg",
             f"{STATIC_ROOT}/bot/img/roulette.jpg"],
            [90, 10])
        photo = self.bot.get_photo_attachment(photo, peer_id=self.event.peer_id, filename="petrovich_roulette.jpg")
        return ResponseMessageItem(attachments=[photo])

    def menu_bonus(self) -> ResponseMessageItem:
        datetime_now = localize_datetime(datetime.datetime.utcnow(), DEFAULT_TIME_ZONE)
        datetime_last = localize_datetime(remove_tz(self.gamer.roulette_points_today), DEFAULT_TIME_ZONE)
        if (datetime_now.date() - datetime_last.date()).days <= 0:
            raise PWarning("Ты уже получил бонус. Приходи завтра")
        self.gamer.roulette_points += 500
        self.gamer.roulette_points_today = datetime_now
        self.gamer.save()
        answer = "Выдал пособие по безработице"
        return ResponseMessageItem(text=answer)

    def menu_transfer(self) -> ResponseMessageItem:
        self.check_conversation()
        self.args = 3
        self.int_args = [-1]
        self.check_args()
        self.parse_int()

        points_transfer = self.event.message.args[-1]
        if points_transfer > self.gamer.roulette_points:
            raise PWarning("Недостаточно очков")
        if points_transfer <= 0:
            raise PWarning("Очков должно быть >0")
        user_gamer = self.get_gamer_by_name(self.event.message.args[1:-1])

        if self.gamer == user_gamer:
            raise PWarning("))")

        self.gamer.roulette_points -= points_transfer
        self.gamer.save()
        user_gamer.roulette_points += points_transfer
        user_gamer.save()

        answer = f"Передал игроку {user_gamer.profile} {points_transfer} {decl_of_num(points_transfer, ['очко', 'очка', 'очков'])}"
        return ResponseMessageItem(text=answer)

    def menu_give(self) -> ResponseMessageItem:
        self.check_sender(Role.ADMIN)
        self.check_conversation()
        self.args = 3
        self.int_args = [-1]
        self.check_args()
        self.parse_int()

        points_transfer = self.event.message.args[-1]

        user_gamer = self.get_gamer_by_name(self.event.message.args[1:-1])

        user_gamer.roulette_points += points_transfer
        user_gamer.save()
        if points_transfer > 0:
            answer = f"Начислил игроку {user_gamer.profile} {points_transfer} " \
                     f"{decl_of_num(points_transfer, ['очко', 'очка', 'очков'])}"
            return ResponseMessageItem(text=answer)
        elif points_transfer < 0:
            answer = f"Забрал у игрока {user_gamer.profile} {-points_transfer} " \
                     f"{decl_of_num(-points_transfer, ['очко', 'очка', 'очков'])}"
            return ResponseMessageItem(text=answer)
        answer = "ммм"
        return ResponseMessageItem(text=answer)

    def menu_rates(self) -> ResponseMessageItem:
        rrs = self.get_active_rates()

        answer = ""
        for rr in rrs:
            rate_on_dict = rr.rate_on
            answer += f"{rr.gamer.profile} поставил на {rate_on_dict['verbose_name']} {rr.rate} очков\n"
        return ResponseMessageItem(text=answer)

    def menu_rate_on(self) -> ResponseMessageItem:
        rate_on = self.event.message.args[0]
        if rate_on not in TRANSLATOR:
            raise PWarning(f"Не могу понять на что вы поставили. {self.bot.get_formatted_text_line('/ман рулетка')}")
        self.args = 2
        self.check_args()
        if self.event.message.args[-1] == 'все':
            rate = self.gamer.roulette_points
        else:
            self.int_args = [-1]
            self.parse_int()
            rate = self.event.message.args[-1]
        if rate <= 0:
            raise PWarning("Ставка не может быть ⩽0")
        if rate > self.gamer.roulette_points:
            raise PWarning(f"Ставка не может быть больше ваших очков - {self.gamer.roulette_points}")

        if rate_on in ['строка', 'столбец']:
            self.args = 3
            self.int_args = [1, 2]
            self.check_args()
            self.parse_int()
            row_col = self.event.message.args[1]
            self.check_number_arg_range(row_col, 1, 3)

            rate_obj = TRANSLATOR[rate_on][row_col]
        else:
            rate_obj = TRANSLATOR[rate_on]
        rr = RouletteRate(gamer=self.gamer, chat=self.event.chat, rate_on=rate_obj, rate=rate)
        rr.save()
        self.gamer.roulette_points -= rate
        self.gamer.save()

        answer = "Поставил"
        return ResponseMessageItem(text=answer)

    def menu_play(self) -> ResponseMessageItem:
        with lock:
            rrs = self.get_active_rates()
            msg1 = "Ставки сделаны. Ставок больше нет\n"
            roulette_ball = get_random_int(MAX_NUMBERS)
            msg2 = f"Крутим колесо. Выпало - {roulette_ball}\n\n"

            winners = []
            for rr in rrs:
                rate_on = rr.rate_on
                if roulette_ball in rate_on['win_numbers']:
                    win_points = rr.rate * rate_on['coefficient']
                    rr.gamer.roulette_points += win_points
                    rr.gamer.save()
                    winners.append({'user': rr.gamer.profile, 'points': win_points})
            if len(winners) > 0:
                msg3 = "Победители:\n"
                for winner in winners:
                    msg3 += f"{winner['user']} - {winner['points']}\n"
            else:
                msg3 = "Нет победителей"
            answer = msg1 + msg2 + msg3
            rrs.delete()
            return ResponseMessageItem(text=answer)

    def get_gamer_by_name(self, username):
        user = self.bot.get_profile_by_name([username], self.event.chat)
        if not user.gamer:
            raise PWarning("Не нашёл такого игрока")
        return user.gamer

    def get_active_rates(self):
        if self.event.is_from_chat:
            rrs = RouletteRate.objects.filter(chat=self.event.chat)
        else:
            rrs = RouletteRate.objects.filter(chat__isnull=True, gamer=self.gamer)
        if len(rrs) == 0:
            raise PWarning("Ставок нет")
        return rrs
