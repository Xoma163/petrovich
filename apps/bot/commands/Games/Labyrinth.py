import json
from threading import Lock

from apps.bot.APIs.EdubovitLabyrinthAPI import EdubovitLabyrinthAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.classes.consts.Exceptions import PSkip

lock = Lock()

DIGITS_IN_GAME = 4


class BullsAndCows(Command):
    name = "лабиринт"
    name_tg = "labyrinth"
    help_text = "игра, где нужно пройти лабиринт."
    help_texts = [
        "- создаёт новую игру"
    ]
    access = Role.GAMER
    platforms = [Platform.TG]

    def start(self):
        if self.event.payload:
            with lock:
                return self.do_the_move()
        else:
            return self.init_game()

    def init_game(self):
        el_api = EdubovitLabyrinthAPI()
        r = el_api.init(10, 10)
        game_id = str(r['id'])
        map_url = el_api.BASE_URL + r['mapUrl']
        keyboard = self.get_keyboard(game_id)
        photo = self.bot.upload_photos(map_url, allowed_exts_url=False)
        return {'attachments': photo, "keyboard": keyboard}

    def do_the_move(self):
        kwargs = self.event.payload['k']
        if 'dir' not in kwargs:
            raise PSkip()
        _dir = kwargs['dir']

        kb = self.event.raw['callback_query']['message']['reply_markup']['inline_keyboard']
        game_id = json.loads(kb[0][0]['callback_data'])['k']['id'] + json.loads(kb[0][2]['callback_data'])['k']['id']
        el_api = EdubovitLabyrinthAPI()
        r = el_api.do_the_move(game_id, kwargs['dir'])

        if not r['successMove']:
            raise PSkip()

        photo = self.bot.upload_photos(el_api.BASE_URL + r['mapUrl'], allowed_exts_url=False)
        message_id = self.event.raw['callback_query']['message']['message_id']
        keyboard = self.get_keyboard(game_id)

        if r['finish']:
            self.win()
            for row in keyboard['inline_keyboard']:
                for button in row:
                    button['callback_data'] = "{}"
        return {'attachments': photo, 'message_id': message_id, 'keyboard': keyboard}

    def win(self):
        gamer = self.bot.get_gamer_by_profile(self.event.sender)
        gamer.roulette_points += 3000
        gamer.save()
        self.bot.parse_and_send_msgs("Ура, вы прошли лабиринт! Получите и распишитесь - 3000 очков ваши",
                                     self.event.peer_id)

    def get_keyboard(self, game_id: str):
        up_button = self.bot.get_button('↑', self.name_tg, kwargs={'dir': 'up'})
        down_button = self.bot.get_button('↓', self.name_tg, kwargs={'dir': 'down'})
        left_button = self.bot.get_button('←', self.name_tg, kwargs={'dir': 'left'})
        right_button = self.bot.get_button('→', self.name_tg, kwargs={'dir': 'right'})
        left_empty_button = self.bot.get_button(' ', self.name_tg, kwargs={'id': game_id[:len(game_id) // 2]})
        right_empty_button = self.bot.get_button(' ', self.name_tg, kwargs={'id': game_id[len(game_id) // 2:]})

        buttons = [
            left_empty_button, up_button, right_empty_button,
            left_button, down_button, right_button
        ]
        keyboard = self.bot.get_inline_keyboard(buttons, 3)
        return keyboard
