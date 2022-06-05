import itertools
import json
import random
from copy import deepcopy

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from apps.bot.utils.utils import random_event


class Minesweeper(Command):
    name = "сапер"
    help_text = "игра сапёр"
    platforms = [Platform.TG]

    def __init__(self):
        super().__init__()

        self.width: int = 8
        self.height: int = 8
        self.mines: int = 9
        self.board = []

        self.emoji_map = {
            -1: "🚩",
            0: "▪",
            1: "1️⃣",
            2: "2️⃣",
            3: "3️⃣",
            4: "4️⃣",
            5: "5️⃣",
            6: "6️⃣",
            7: "7️⃣",
            8: "8️⃣",
            9: "9️⃣",
        }

    def start(self):
        args = self.event.message.args

        if 'callback_query' in self.event.raw and args:
            inline_keyboard = self.event.raw['callback_query']['message']['reply_markup']['inline_keyboard']

            return self.press_the_button(int(args[0]), int(args[1]), int(args[2]), inline_keyboard)
        else:
            return self.send_init_keyboard()

    def generate(self):
        self.board = [[0 for _ in range(self.width)] for _ in range(self.height)]

        # random mines
        width_pool = [x for x in range(self.width)]
        height_pool = [y for y in range(self.height)]
        mines_pos_pool = [(x[0], x[1]) for x in itertools.product(height_pool, width_pool)]
        for _ in range(self.mines):
            x, y = random.choice(mines_pos_pool)
            self.board[x][y] = -1

        for x in range(self.height):
            for y in range(self.width):
                if self.board[x][y] == -1:
                    self._increase_rectangle(x, y)

    def _increase_rectangle(self, x, y):
        x_val = [_x for _x in range(x - 1, x + 2) if 0 <= _x < self.height]
        y_val = [_y for _y in range(y - 1, y + 2) if 0 <= _y < self.width]
        positions = itertools.product(x_val, y_val)

        for pos in positions:
            i, j = pos
            if i == x and j == y:
                continue
            if self.board[i][j] == -1:
                continue
            self.board[i][j] += 1

    def send_init_keyboard(self):
        self.generate()
        buttons = []
        for i in range(self.height):
            for j in range(self.width):
                button_text = "     "
                button = self.bot.get_button(button_text, self.name, (i, j, self.board[i][j], False))
                buttons.append(button)
        keyboard = self.bot.get_inline_keyboard(buttons, self.width)
        return {'text': 'Сапёр', "keyboard": keyboard}

    def press_the_button(self, i, j, val, inline_keyboard):
        if val == -1:
            return self.game_over(inline_keyboard)

        self.height = len(inline_keyboard)
        self.width = len(inline_keyboard[0])
        message_id = self.event.raw['callback_query']['message']['message_id']

        self.propagate(i, j, inline_keyboard)

        win = self.check_win(inline_keyboard)
        if win:
            return win

        return {"keyboard": {"inline_keyboard": inline_keyboard}, "message_id": message_id}

    def propagate(self, i, j, inline_keyboard):
        if i < 0 or i >= self.height:
            return
        if j < 0 or j >= self.width:
            return
        data = json.loads(inline_keyboard[i][j]['callback_data'])
        x, y, val, state = data['args']
        inline_keyboard[i][j]['text'] = self.emoji_map[val]
        if data['args'][3]:
            return
        data['args'][3] = True
        inline_keyboard[i][j]['callback_data'] = json.dumps(data, ensure_ascii=False)
        if val == 0:
            self.propagate(i, j + 1, inline_keyboard)
            self.propagate(i + 1, j, inline_keyboard)
            self.propagate(i, j - 1, inline_keyboard)
            self.propagate(i - 1, j, inline_keyboard)

    def game_over(self, inline_keyboard):
        first_try = True
        for i in range(len(inline_keyboard)):
            for j in range(len(inline_keyboard[i])):
                _, _, val, opened = json.loads(inline_keyboard[i][j]['callback_data'])['args']
                button_text = self.emoji_map[val]
                first_try &= not opened
                inline_keyboard[i][j]['callback_data'] = "{}"
                inline_keyboard[i][j]['text'] = button_text
        message_id = self.event.raw['callback_query']['message']['message_id']

        if first_try:
            text = random_event(
                ["Жизнь вообще несправедливая штука",
                 "Сапёр ошибается один раз",
                 "Просто за тобой были грехи",
                 "Не повезло в сапёре - повезёт в любви"]
            )
        else:
            text = '*хлопок*'
        return {'text': text, "keyboard": {"inline_keyboard": inline_keyboard}, 'message_id': message_id}

    def check_win(self, inline_keyboard):
        inline_keyboard_copy = deepcopy(inline_keyboard)
        for i in range(len(inline_keyboard)):
            for j in range(len(inline_keyboard[i])):
                _, _, val, opened = json.loads(inline_keyboard[i][j]['callback_data'])['args']
                if val != -1 and not opened:
                    return
                button_text = self.emoji_map[val]
                inline_keyboard_copy[i][j]['callback_data'] = "{}"
                inline_keyboard_copy[i][j]['text'] = button_text
        message_id = self.event.raw['callback_query']['message']['message_id']
        text = 'Вы победили!'
        return {'text': text, "keyboard": {"inline_keyboard": inline_keyboard_copy}, 'message_id': message_id}
