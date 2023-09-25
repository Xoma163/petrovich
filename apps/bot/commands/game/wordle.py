import json
import os
from threading import Lock

from PIL import ImageFont, Image, ImageDraw

from apps.bot.classes.bots.tg import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Platform, Role, rus_alphabet
from apps.bot.classes.const.exceptions import PWarning, PSkip
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.utils.utils import random_event, _send_message_session_or_edit
from apps.games.models import Wordle as WordleModel
from petrovich.settings import STATIC_ROOT

lock = Lock()


class Wordle(Command):
    name = "wordle"
    names = ['вордле']
    name_tg = 'wordle'

    help_text = "игра wordle"
    help_texts = [
        "- запуск сессии игры",
        "сдаться - удаление сессии",
        "(слово из 5 букв) - попытка угадать слово"
    ]
    help_texts_extra = "[] означает, что буква стоит на месте\n() означает, что буква присутствует в слове"

    platforms = [Platform.TG]
    access = Role.GAMER

    bot: TgBot

    MAX_STEPS = 6
    WORDLE_WORDS_PATH = "static/bot/games/wordle/wordle.json"

    # ToDo: self.session
    def start(self) -> ResponseMessage:
        if self.event.message.args:
            arg0 = self.event.message.args[0]
        else:
            arg0 = None
        menu = [
            [[None], self.start_session],
            [['сдаться'], self.lose],
            [['default'], self.hypothesis]
        ]
        method = self.handle_menu(menu, arg0)
        rmi = method()
        return ResponseMessage(rmi)

    def start_session(self) -> ResponseMessageItem:
        existed_session = self.get_session()
        if existed_session:
            self.get_current_state(existed_session)
            raise PSkip()

        data = {
            "word": self.get_random_word(),
            "steps": 0,
            "hypotheses": []
        }

        if self.event.is_from_chat:
            data['chat'] = self.event.chat
        else:
            data['profile'] = self.event.sender
        WordleModel.objects.create(**data)

        answer = "Игра начата. Поехали!"
        return ResponseMessageItem(text=answer)

    def hypothesis(self):
        hypothesis = self.event.message.args[0]
        session = self.get_session()
        if not session:
            self._raise_start_game()

        hypothesis = "".join([x for x in hypothesis if x.isalpha() and x in rus_alphabet])
        if len(hypothesis) != 5:
            raise PWarning("Слово должно состоять из 5 букв")

        session.hypotheses.append(hypothesis)
        session.steps += 1
        session.save()

        if hypothesis == session.word:
            return self.win()

        if len(session.hypotheses) > 5:
            return self.lose()

        self.get_current_state(session)

    def get_current_state(self, session):
        image = self.get_keyboard_image(session)
        attachment = self.bot.get_photo_attachment(image)
        rmi = ResponseMessageItem(attachments=[attachment], peer_id=self.event.peer_id,
                                  message_thread_id=self.event.message_thread_id)
        _send_message_session_or_edit(self.bot, self.event, session, rmi, max_delta=8)

    def get_random_word(self):
        with open(self.WORDLE_WORDS_PATH, 'r') as f:
            words = json.loads(f.read())
        return random_event(words)

    def get_session(self) -> WordleModel:
        if self.event.is_from_chat:
            return WordleModel.objects.filter(chat=self.event.chat).first()
        else:
            return WordleModel.objects.filter(profile=self.event.sender).first()

    @staticmethod
    def calculate_words(hypothesis, answer):
        correct_letters = []
        exactly_correct_letters = []
        wrong_letters = []
        for i, letter in enumerate(hypothesis):
            for j, letter2 in enumerate(answer):
                if letter == letter2:
                    if i == j:
                        exactly_correct_letters.append(i)
                    else:
                        correct_letters.append(i)
            if i not in correct_letters and i not in exactly_correct_letters:
                wrong_letters.append(i)
        return correct_letters, exactly_correct_letters, wrong_letters

    def get_keyboard_image(self, session):
        correct_letters = set()
        exactly_correct_letters = set()
        wrong_letters = set()
        for word in session.hypotheses:
            cl, ecl, wl = self.calculate_words(word, session.word)
            for i in ecl:
                exactly_correct_letters.add(word[i])
            for i in cl:
                correct_letters.add(word[i])
            for i in wl:
                wrong_letters.add(word[i])

        for letter in exactly_correct_letters:
            if letter in correct_letters:
                correct_letters.remove(letter)

        wig = WordleImageGenerator()
        image = wig.generate(session.hypotheses, correct_letters, exactly_correct_letters, wrong_letters, session.word)

        return image

    def win(self) -> ResponseMessageItem:
        session = self.get_session()
        word = session.word

        gamer = self.bot.get_gamer_by_profile(self.event.sender)
        gamer.roulette_points += 1000
        gamer.wordle_points += 1
        gamer.save()

        text = f"Вы победили! Загаданное слово - {word}\n" \
               f"Начислил 1000 очков рулетки"

        return self._end_game(session, text)

    def lose(self) -> ResponseMessageItem:
        session = self.get_session()
        if not session:
            self._raise_start_game()
        text = f"Загаданное слово - {session.word}"
        return self._end_game(session, text)

    def _end_game(self, session, text):
        button = self.bot.get_button("Ещё", self.name)
        keyboard = self.bot.get_inline_keyboard([button])

        image = self.get_keyboard_image(session)
        attachment = self.bot.get_photo_attachment(image)
        rmi = ResponseMessageItem(attachments=[attachment], peer_id=self.event.peer_id,
                                  message_thread_id=self.event.message_thread_id)
        _send_message_session_or_edit(self.bot, self.event, session, rmi, max_delta=8)
        session.delete()

        # Зачем?
        return ResponseMessageItem(text=text, keyboard=keyboard)

    def _raise_start_game(self):
        button = self.bot.get_button("Начать", "wordle")
        keyboard = self.bot.get_inline_keyboard([button])
        raise PWarning("Игра не начата! Начните её", keyboard=keyboard)


class WordleImageGenerator:
    COLOR_CORRECT_LETTER_POS = "#538d4e"
    COLOR_CORRECT_LETTER = "#b59f3b"
    COLOR_TEXT = "#ffffff"
    COLOR_DEFAULT = "#818384"
    COLOR_WRONG_LETTER = "#3a3a3c"
    COLOR_BACKGROUND = "#121213"

    MAIN_WINDOW_CELL_WIDTH = 80
    MAIN_WINDOW_CELL_HEIGHT = 80
    MAIN_WINDOW_CELL_MARGIN = 10
    MAIN_WINDOW_CELL_THICKNESS = 2

    MAIN_WINDOW_KEYBOARD_MARGIN = 40

    KEYBOARD_CELL_WIDTH = 35
    KEYBOARD_CELL_HEIGHT = 50
    KEYBOARD_CELL_MARGIN = 10

    MAIN_WINDOW_CELLS_COUNT = 6
    MAIN_WINDOW_CELLS_WORDS_COUNT = 5

    MAIN_WINDOW_WIDTH = MAIN_WINDOW_CELLS_WORDS_COUNT * MAIN_WINDOW_CELL_WIDTH + (
            MAIN_WINDOW_CELLS_WORDS_COUNT - 1) * MAIN_WINDOW_CELL_MARGIN
    MAIN_WINDOW_HEIGHT = MAIN_WINDOW_CELLS_COUNT * MAIN_WINDOW_CELL_HEIGHT + (
            MAIN_WINDOW_CELLS_COUNT - 1) * MAIN_WINDOW_CELL_MARGIN

    KEYBOARD_WIDTH = 12 * KEYBOARD_CELL_WIDTH + (12 - 1) * MAIN_WINDOW_CELL_MARGIN
    KEYBOARD_HEIGHT = 3 * KEYBOARD_CELL_HEIGHT + (3 - 1) * MAIN_WINDOW_CELL_MARGIN

    PADDING = 25

    FONT_PATH = os.path.join(STATIC_ROOT, 'fonts/Intro.otf')

    def generate(self, words, correct_letters, exactly_correct_letters, wrong_letters, secret_word):
        image_words = self.generate_words(words, secret_word)
        image_keyboard = self.generate_keyboard(correct_letters, exactly_correct_letters, wrong_letters)

        width_diff = image_keyboard.width - image_words.width

        dst = Image.new('RGBA', (image_keyboard.width, image_words.height + image_keyboard.height),
                        self.COLOR_BACKGROUND)
        dst.paste(image_words, (int(width_diff / 2), 0))
        dst.paste(image_keyboard, (0, image_words.height))
        return dst

    def generate_words(self, words: list, secret_word):
        image = Image.new("RGBA", (self.MAIN_WINDOW_WIDTH, self.MAIN_WINDOW_HEIGHT), self.COLOR_BACKGROUND)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(self.FONT_PATH, self.MAIN_WINDOW_CELL_WIDTH - 10, encoding="unic")

        for i in range(0, self.MAIN_WINDOW_CELLS_COUNT):
            word = None
            if len(words) > i:
                word = words[i]
            for j in range(0, self.MAIN_WINDOW_CELLS_WORDS_COUNT):
                letter = None
                if word:
                    letter = word[j]
                x1 = j * self.MAIN_WINDOW_CELL_WIDTH + j * self.MAIN_WINDOW_CELL_MARGIN
                y1 = i * self.MAIN_WINDOW_CELL_HEIGHT + i * self.MAIN_WINDOW_CELL_MARGIN
                x2 = j * self.MAIN_WINDOW_CELL_WIDTH + j * self.MAIN_WINDOW_CELL_MARGIN + self.MAIN_WINDOW_CELL_WIDTH
                y2 = i * self.MAIN_WINDOW_CELL_HEIGHT + i * self.MAIN_WINDOW_CELL_MARGIN + self.MAIN_WINDOW_CELL_HEIGHT

                color = self.COLOR_DEFAULT
                if letter:
                    if letter == secret_word[j]:
                        color = self.COLOR_CORRECT_LETTER_POS
                    elif letter in secret_word:
                        color = self.COLOR_CORRECT_LETTER
                    elif letter not in secret_word:
                        color = self.COLOR_WRONG_LETTER
                draw.rectangle((x1, y1, x2, y2), color)
                if letter:
                    letter_width = font.getlength(letter)
                    letter_margin = (self.MAIN_WINDOW_CELL_WIDTH - letter_width) / 2
                    draw.text((x1 + letter_margin, y1 + 11), letter.upper(), font=font, fill=self.COLOR_TEXT)

        dst = Image.new('RGBA', (image.width + self.PADDING * 2, image.height + self.PADDING * 2),
                        self.COLOR_BACKGROUND)
        dst.paste(image, (self.PADDING, self.PADDING))
        return dst

    def generate_keyboard(self, correct_letters, exactly_correct_letters, wrong_letters):
        layouts = [
            ["й", "ц", "у", "к", "е", "н", "г", "ш", "щ", "з", "х", "ъ"],
            ["ф", "ы", "в", "а", "п", "р", "о", "л", "д", "ж", "э"],
            ["я", "ч", "с", "м", "и", "т", "ь", "б", "ю"]
        ]

        image = Image.new("RGBA", (self.KEYBOARD_WIDTH, self.KEYBOARD_HEIGHT), self.COLOR_BACKGROUND)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(self.FONT_PATH, self.KEYBOARD_CELL_WIDTH, encoding="unic")

        for i, row in enumerate(layouts):

            total_width = len(row) * self.KEYBOARD_CELL_WIDTH + (len(row) - 1) * self.MAIN_WINDOW_CELL_MARGIN
            left_margin = (self.KEYBOARD_WIDTH - total_width) / 2
            for j, letter in enumerate(row):
                x1 = j * self.KEYBOARD_CELL_WIDTH + j * self.KEYBOARD_CELL_MARGIN
                y1 = i * self.KEYBOARD_CELL_HEIGHT + i * self.KEYBOARD_CELL_MARGIN
                x2 = j * self.KEYBOARD_CELL_WIDTH + j * self.KEYBOARD_CELL_MARGIN + self.KEYBOARD_CELL_WIDTH
                y2 = i * self.KEYBOARD_CELL_HEIGHT + i * self.KEYBOARD_CELL_MARGIN + self.KEYBOARD_CELL_HEIGHT

                color = self.COLOR_DEFAULT
                if letter:
                    if letter in exactly_correct_letters:
                        color = self.COLOR_CORRECT_LETTER_POS
                    elif letter in correct_letters:
                        color = self.COLOR_CORRECT_LETTER
                    elif letter in wrong_letters:
                        color = self.COLOR_WRONG_LETTER

                draw.rectangle((x1 + left_margin, y1, x2 + left_margin, y2), color)

                letter_width = font.getlength(letter)
                letter_margin = (self.KEYBOARD_CELL_WIDTH - letter_width) / 2
                draw.text((x1 + letter_margin + left_margin, y1 + 10), letter.upper(), font=font, fill=self.COLOR_TEXT)

        dst = Image.new('RGBA', (image.width + self.PADDING * 2, image.height + self.PADDING * 2),
                        self.COLOR_BACKGROUND)
        dst.paste(image, (self.PADDING, self.PADDING))
        return dst
