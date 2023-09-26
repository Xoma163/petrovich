import itertools
import json
import random
from copy import deepcopy
from threading import Lock

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Platform, Role
from apps.bot.classes.const.exceptions import PSkip
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.utils.utils import random_event

lock = Lock()


class Minesweeper(Command):
    MODE_DEFAULT = 0
    MODE_MINES = 1

    MINE = -1
    EMPTY = 0

    name = "сапер"
    help_text = "игра сапёр"
    help_texts = ["[кол-во мин=10] - запускает игру в сапёра"]
    platforms = [Platform.TG]
    access = Role.GAMER

    bot: TgBot

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.width: int = 8
        self.height: int = 12
        self.mines: int = 10
        self.board = []
        self.mode = self.MODE_DEFAULT

        self.flag = "🏳️"

        self.emoji_map = {
            self.MINE: "🚩",
            self.EMPTY: "▪",
            1: "1️⃣",
            2: "2️⃣",
            3: "3️⃣",
            4: "4️⃣",
            5: "5️⃣",
            6: "6️⃣",
            7: "7️⃣",
            8: "8️⃣",
        }
        self.message_id = None

    # x, y, real_val, flag_val, opened

    def start(self) -> ResponseMessage:
        with lock:

            if 'callback_query' in self.event.raw:
                self.message_id = self.event.raw['callback_query']['message']['message_id']

            args = self.event.message.args
            kwargs = self.event.message.kwargs
            if kwargs and "mode" in kwargs:
                inline_keyboard = self.event.raw['callback_query']['message']['reply_markup']['inline_keyboard']
                return self.press_switch_mode_button(inline_keyboard)
            elif 'callback_query' in self.event.raw and args:
                inline_keyboard = self.event.raw['callback_query']['message']['reply_markup']['inline_keyboard']
                _args = self.event.payload['a']
                if len(_args) == 1:
                    self.mines = min(self.width * self.height - 1, int(_args[0]))
                    self.mines = max(0, self.mines)
                    return self.send_init_keyboard()
                _args = [int(arg) for arg in _args]
                return self.press_button(*_args, inline_keyboard)
            else:
                if args:
                    self.int_args = [0]
                    self.parse_int()
                    self.mines = min(self.width * self.height - 1, int(args[0]))
                    self.mines = max(1, self.mines)

                return self.send_init_keyboard()

    def generate(self):
        self.board = [[self.EMPTY for _ in range(self.width)] for _ in range(self.height)]
        # random mines
        width_pool = [x for x in range(self.width)]
        height_pool = [y for y in range(self.height)]
        mines_pos_pool = [(x[0], x[1]) for x in itertools.product(height_pool, width_pool)]
        for _ in range(self.mines):
            pos = random.choice(mines_pos_pool)
            mines_pos_pool.remove(pos)
            x, y = pos
            self.board[x][y] = self.MINE

        for x in range(self.height):
            for y in range(self.width):
                if self.board[x][y] == -1:
                    self._increase_rectangle(x, y)

    def _increase_rectangle(self, x, y):
        positions = self._get_rectangle_pos(x, y)

        for pos in positions:
            i, j = pos
            if i == x and j == y:
                continue
            if self.board[i][j] == -1:
                continue
            self.board[i][j] += 1

    def send_init_keyboard(self) -> ResponseMessage:
        self.generate()
        buttons = []
        for i in range(self.height):
            for j in range(self.width):
                button_text = "     "
                button = self.bot.get_button(button_text, self.name, [i, j, self.board[i][j], 0, 0])
                buttons.append(button)
        keyboard = self.bot.get_inline_keyboard(buttons, self.width)

        button = self.bot.get_button(f"Включить режим планирования {self.flag}", self.name,
                                     kwargs={'mode': self.MODE_MINES})
        keyboard['inline_keyboard'].append([button])

        answer = f'Сапёр - {self.mines} мин'
        return ResponseMessage(ResponseMessageItem(text=answer, keyboard=keyboard, message_id=self.message_id))

    def press_switch_mode_button(self, inline_keyboard) -> ResponseMessage:
        self.mode = self.event.payload['k']['mode']
        self._edit_mode_button(inline_keyboard)
        keyboard = {"inline_keyboard": inline_keyboard}
        return ResponseMessage(ResponseMessageItem(keyboard=keyboard, message_id=self.message_id))

    def press_button(self, i, j, real_val, _, opened, inline_keyboard) -> ResponseMessage:
        callback_data_mines = json.loads(inline_keyboard[-1][0]['callback_data'])['k']['mode']
        self.mode = self.MODE_DEFAULT if callback_data_mines == self.MODE_MINES else self.MODE_MINES
        self.height = len(inline_keyboard) - 1
        self.width = len(inline_keyboard[0])

        if opened == 1:
            return self.press_opened_button(i, j, real_val, inline_keyboard)

        if self.mode == self.MODE_MINES:
            return self.press_button_in_mines_mode(i, j, opened, inline_keyboard)

        if real_val == self.MINE:
            return self.game_over(inline_keyboard)

        self.propagate(i, j, inline_keyboard)

        win = self.check_win(inline_keyboard)
        if win:
            return win
        self._edit_mode_button(inline_keyboard)

        keyboard = {"inline_keyboard": inline_keyboard}
        return ResponseMessage(ResponseMessageItem(keyboard=keyboard, message_id=self.message_id))

    def press_opened_button(self, i, j, real_val, inline_keyboard) -> ResponseMessage:
        positions = list(self._get_rectangle_pos(i, j))
        flags = 0
        for position in positions:
            x, y = position
            callback_data = json.loads(inline_keyboard[x][y]['callback_data'])
            _, _, _, _flag_val, _ = callback_data['a']
            if _flag_val == 1:
                flags += 1

        if real_val != flags:
            raise PSkip()

        one_updated = False
        for position in positions:
            x, y = position
            if x == i and j == y:
                continue
            callback_data = json.loads(inline_keyboard[x][y]['callback_data'])
            _i, _j, _real_val, _flag_val, _opened = callback_data['a']
            if _opened:
                continue
            if _real_val == self.MINE and _flag_val == 1:
                continue
            if _real_val == self.MINE:
                return self.game_over(inline_keyboard)

            self.propagate(_i, _j, inline_keyboard)
            one_updated = True
        if not one_updated:
            raise PSkip()

        win = self.check_win(inline_keyboard)
        if win:
            return win

        keyboard = {"inline_keyboard": inline_keyboard}
        return ResponseMessage(ResponseMessageItem(keyboard=keyboard, message_id=self.message_id))

    def press_button_in_mines_mode(self, i, j, opened, inline_keyboard) -> ResponseMessage:
        if opened:
            return
        callback_data = json.loads(inline_keyboard[i][j]['callback_data'])
        callback_data['a'][3] = 1 if callback_data['a'][3] == 0 else 0
        inline_keyboard[i][j]['callback_data'] = json.dumps(callback_data, ensure_ascii=False)
        inline_keyboard[i][j]['text'] = self.flag if callback_data['a'][3] == 1 else "     "

        keyboard = {"inline_keyboard": inline_keyboard}
        return ResponseMessage(ResponseMessageItem(keyboard=keyboard, message_id=self.message_id))

    def propagate(self, i, j, inline_keyboard):
        if i < 0 or i >= self.height:
            return
        if j < 0 or j >= self.width:
            return
        data = json.loads(inline_keyboard[i][j]['callback_data'])
        _, _, val, _, opened = data['a']
        inline_keyboard[i][j]['text'] = self.emoji_map[val]
        if opened == 1:
            return
        data['a'][4] = 1
        inline_keyboard[i][j]['callback_data'] = json.dumps(data, ensure_ascii=False)
        if val == 0:
            positions = self._get_rectangle_pos(i, j)
            for pos in positions:
                i, j = pos
                self.propagate(i, j, inline_keyboard)

    def game_over(self, inline_keyboard) -> ResponseMessage:
        first_try = True
        for i in range(self.height):
            for j in range(self.width):
                _, _, val, _, opened = json.loads(inline_keyboard[i][j]['callback_data'])['a']
                button_text = self.emoji_map[val]
                first_try &= not bool(opened)
                inline_keyboard[i][j]['callback_data'] = "{}"
                inline_keyboard[i][j]['text'] = button_text

        if first_try:
            text = random_event(
                ["Жизнь вообще несправедливая штука",
                 "Сапёр ошибается один раз",
                 "Просто за тобой были грехи",
                 "Не повезло в сапёре - повезёт в любви"]
            )
            text += "\nДержи 500 утешительных очков"
            gamer = self.bot.get_gamer_by_profile(self.event.sender)
            gamer.roulette_points += 500
            gamer.save()
        else:
            text = '*хлопок*'
        button = self.bot.get_button("Ещё (легко)", self.name, [10])
        button2 = self.bot.get_button("Ещё (средне)", self.name, [18])
        button3 = self.bot.get_button("Ещё (сложно)", self.name, [25])
        inline_keyboard[-1] = [button, button2, button3]

        keyboard = {"inline_keyboard": inline_keyboard}
        return ResponseMessage(ResponseMessageItem(text=text, keyboard=keyboard, message_id=self.message_id))

    def check_win(self, inline_keyboard) -> ResponseMessage:
        inline_keyboard_copy = deepcopy(inline_keyboard)
        mines_count = 0
        for i in range(self.height):
            for j in range(self.width):
                _, _, val, _, opened = json.loads(inline_keyboard[i][j]['callback_data'])['a']
                if val != -1 and not opened:
                    return
                if val == -1:
                    mines_count += 1
                button_text = self.emoji_map[val]
                inline_keyboard_copy[i][j]['callback_data'] = "{}"
                inline_keyboard_copy[i][j]['text'] = button_text
        text = 'Вы победили!'
        button = self.bot.get_button("Ещё (легко)", self.name, [10])
        button2 = self.bot.get_button("Ещё (средне)", self.name, [18])
        button3 = self.bot.get_button("Ещё (сложно)", self.name, [25])
        inline_keyboard_copy[-1] = [button, button2, button3]
        if mines_count >= 10:
            prize = self.mines * 300
            gamer = self.bot.get_gamer_by_profile(self.event.sender)
            gamer.roulette_points += prize
            gamer.save()
            text += f"\nНачислил {prize} очков"

        keyboard = {"inline_keyboard": inline_keyboard}
        return ResponseMessage(ResponseMessageItem(text=text, keyboard=keyboard, message_id=self.message_id))

    def _edit_mode_button(self, inline_keyboard):
        if self.mode == self.MODE_DEFAULT:
            button = self.bot.get_button(f"Включить режим планирования {self.flag}", self.name,
                                         kwargs={'mode': self.MODE_MINES})
        else:
            button = self.bot.get_button(f"Включить обычный режим {self.emoji_map[self.MINE]}", self.name,
                                         kwargs={'mode': self.MODE_DEFAULT})

        inline_keyboard[-1] = [button]

    def _get_rectangle_pos(self, i, j):
        x_val = [_x for _x in range(i - 1, i + 2) if 0 <= _x < self.height]
        y_val = [_y for _y in range(j - 1, j + 2) if 0 <= _y < self.width]
        return itertools.product(x_val, y_val)
