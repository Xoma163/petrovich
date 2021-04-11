import json
from threading import Lock

from django.db.models import Q

from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.games.models import TicTacToeSession, Gamer

MORE_HIDE_KEYBOARD = {
    "one_time": True,
    "buttons": [
        [
            {
                "action": {
                    "type": "text",
                    "label": "Крестики"
                },
                "color": "primary"
            }
        ],
        [
            {
                "action": {
                    "type": "text",
                    "label": "Скрыть"
                },
                "color": "secondary"
            }
        ],
    ]
}

lock = Lock()


# ToDo: TG клавы
class TicTacToe(CommonCommand):
    name = 'крестики'
    names = ["крестики-нолики", "нолики"]
    help_text = "крестики-нолики"
    help_texts = [
        "- крестики-нолики. Игра проходит в лс и управляется с клавиатуры",
        "[строка [столбец]] - ход в это место (если не работает клавиатура)"
    ]
    int_args = [0, 1]
    platforms = [Platform.VK]

    def start(self):
        with lock:
            sender = self.event.sender

            if len(Gamer.objects.filter(user=sender)) == 0:
                Gamer(user=sender).save()

            session = TicTacToeSession.objects.filter(Q(user1=sender) | Q(user2=sender)).first()
            # Если существует такая сессия, где игрок находится в ней
            if session:
                # Если оба игрока существуют в сессии
                if session.user1 is not None and session.user2 is not None:
                    # Если переданы аргументы
                    if self.event.args:
                        # Шаг игры
                        self.step_game(session)
                        return
                    else:
                        # Возвращаем пользователю клавиатуру, если он её потерял
                        self.bot.send_message(sender.user_id, "Да держи ты свою клаву, ё-моё",
                                              keyboard=get_keyboard_by_board(session.board))
                        return
                # Если игрок только один и 99.9% что это user1
                else:
                    return "Ты начал игру. Подожди, когда подключится второй игрок"
            # Если нет такой сессии, в которой есть игрок
            else:
                waiting_session = TicTacToeSession.objects.filter(user2=None).first()
                # Если есть сессия, где пустует второй игрок
                if waiting_session:
                    # То стартуем игру
                    self.start_game(waiting_session)
                    return f"Начинаем игру против {waiting_session.user1}"
                # Никаких свободных сессий нет - создаём новую
                else:
                    TicTacToeSession(user1=sender).save()
                    return "Начинаем игру. Ждём второго игрока"

    def step_game(self, session):
        sender = self.event.sender
        args = self.event.args
        if sender != session.next_step:
            self.bot.send_message(sender.user_id, "Ход второго игрока")
            return

        elem = ''
        if session.user1 == sender:
            elem = 'x'
        elif session.user2 == sender:
            elem = 'o'

        table = session.board
        if table[args[0]][args[1]] != '':
            self.bot.send_message(sender.user_id, "Сюда нельзя ставить")
            return
        else:
            table[args[0]][args[1]] = elem

        res = check_win(table)
        if res:
            session.delete()
            if res == 'x':
                self.end_game(session, table, session.user1)
            elif res == 'o':
                self.end_game(session, table, session.user2)

            return
        elif check_end(table):
            session.delete()
            self.bot.send_message(session.user1.user_id,
                                  f"Ничья\n{print_table(table)}",
                                  keyboard=MORE_HIDE_KEYBOARD)
            self.bot.send_message(session.user2.user_id,
                                  f"Ничья\n{print_table(table)}",
                                  keyboard=MORE_HIDE_KEYBOARD)
            return

        board = get_keyboard_by_board(table)

        if session.next_step == session.user1:
            self.bot.send_message(session.user1.user_id, "Ход сделан, ждём хода второго игрока", keyboard=board)
            self.bot.send_message(session.user2.user_id, "Второй игрок сделал ход", keyboard=board)
            session.next_step = session.user2
        elif session.next_step == session.user2:
            self.bot.send_message(session.user1.user_id, "Второй игрок сделал ход", keyboard=board)
            self.bot.send_message(session.user2.user_id, "Ход сделан, ждём хода второго игрока", keyboard=board)
            session.next_step = session.user1

        session.board = table
        session.save()

    def start_game(self, session):
        session.user2 = self.event.sender
        session.next_step = session.user1
        session.save()
        keyboard = get_keyboard_by_board(session.board)
        self.bot.send_message(session.user1.user_id,
                              f"Второй игрок - {session.user2}\nВаш ход\nВы играете за ❌",
                              keyboard=keyboard)
        self.bot.send_message(session.user2.user_id,
                              f"Второй игрок - {session.user1}\nХод второго игрока\nВы играете за ⭕",
                              keyboard=keyboard)

    def end_game(self, session, table, winner):
        self.bot.send_message(session.user1.user_id,
                              f"Игра закончена. Победитель - {winner}\n"
                              f"{print_table(table)}",
                              keyboard=MORE_HIDE_KEYBOARD)
        self.bot.send_message(session.user2.user_id,
                              f"Игра закончена. Победитель - {winner}\n"
                              f"{print_table(table)}",
                              keyboard=MORE_HIDE_KEYBOARD)
        gamer = Gamer.objects.get(user=session.user1)
        gamer.tic_tac_toe_points += 1
        gamer.save()


def check_win(table):
    for i, _ in enumerate(table):
        res = check_win_elems([row for row in table[i]])
        if res:
            return res
        res = check_win_elems([row[i] for row in table])
        if res:
            return res

    res = check_win_elems([table[i][i] for i, _ in enumerate(table)])
    if res:
        return res

    res = check_win_elems([table[i][len(table[i]) - 1 - i] for i, _ in enumerate(table)])
    if res:
        return res

    return False


def check_win_elems(*args):
    args = args[0]
    val = args[0]
    result = True

    for arg in args:
        result = (arg != '') and (arg == val) and result
        if not result:
            return False

    return val


def check_end(table):
    for row in table:
        for elem in row:
            if elem == '':
                return False
    return True


def get_keyboard_by_board(table):
    buttons = []
    for i, row in enumerate(table):
        rows = []
        for j, elem in enumerate(row):
            rows.append(get_elem(elem, i, j))
        buttons.append(rows)

    keyboard = {
        "one_time": False,
        "buttons": buttons
    }
    return keyboard


def get_elem(elem, row, col):
    if elem == 'x':
        label = "❌"
    elif elem == 'o':
        label = "⭕"
    else:
        label = "ᅠ"

    return {
        "action": {
            "type": "text",
            "label": label,
            "payload": json.dumps({"command": "крестики", "args": {"row": row, "col": col}}, ensure_ascii=False)
        },
        "color": "secondary"
    }


def print_table(table):
    result = ""
    for row in table:
        rows = ""
        for elem in row:
            if elem == '':
                elem = '—'
            rows += elem.upper()
        result += rows + "\n"
    return result
