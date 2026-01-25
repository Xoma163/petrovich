import json
from threading import Lock

from PIL import Image, ImageDraw

from apps.bot.consts import PlatformEnum, RoleEnum
from apps.bot.core.bot.tg_bot.tg_bot import TgBot
from apps.bot.core.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.commands.command import Command
from apps.commands.games.models import Wordle as WordleModel
from apps.commands.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.shared.consts import rus_alphabet
from apps.shared.exceptions import PWarning, PSkip
from apps.shared.utils.utils import random_event, get_font_by_path, convert_pil_image_to_bytes

lock = Lock()


class Wordle(Command):
    name = "wordle"
    names = ['вордле']

    help_text = HelpText(
        commands_text="игра wordle",
        help_texts=[
            HelpTextItem(RoleEnum.USER, [
                HelpTextArgument(None, "запуск сессии игры"),
                HelpTextArgument("сдаться", "удаление сессии"),
                HelpTextArgument("(слово из 5 букв)", "попытка угадать слово")
            ])
        ],
        extra_text=(
            "[] означает, что буква стоит на месте\n() означает, что буква присутствует в слове"
        )
    )

    platforms = [PlatformEnum.TG]

    bot: TgBot

    MAX_STEPS = 6
    WORDLE_WORDS_PATH = "static/games/wordle/wordle.json"

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
        return None

    def get_current_state(self, session) -> ResponseMessage:
        image = self.get_keyboard_image(session)
        attachment = self.bot.get_photo_attachment(
            _bytes=image,
            peer_id=self.event.peer_id
        )
        rmi = ResponseMessageItem(attachments=[attachment], peer_id=self.event.peer_id,
                                  message_thread_id=self.event.message_thread_id)
        send_message_session_or_edit(self.bot, self.event, session, rmi, max_delta=8)
        return ResponseMessage(rmi, send=False)

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

        text = f"Вы победили! Загаданное слово - {word}\n" \
               f"Начислил 1000 очков рулетки"

        return self._end_game(session, text)

    def lose(self) -> ResponseMessageItem:
        session = self.get_session()
        if not session:
            self._raise_start_game()
        text = f"Загаданное слово - {session.word}"
        return self._end_game(session, text)

    def _end_game(self, session: WordleModel, text):
        button = self.bot.get_button("Ещё", self.name)
        keyboard = self.bot.get_inline_keyboard([button])

        image = self.get_keyboard_image(session)
        attachment = self.bot.get_photo_attachment(image)
        rmi = ResponseMessageItem(attachments=[attachment], peer_id=self.event.peer_id,
                                  message_thread_id=self.event.message_thread_id)
        send_message_session_or_edit(self.bot, self.event, session, rmi, max_delta=8)
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

    FONT_NAME = "Intro.otf"

    def generate(self, words, correct_letters, exactly_correct_letters, wrong_letters, secret_word) -> bytes:
        image_words = self.generate_words(words, secret_word)
        image_keyboard = self.generate_keyboard(correct_letters, exactly_correct_letters, wrong_letters)

        width_diff = image_keyboard.width - image_words.width

        dst = Image.new('RGBA', (image_keyboard.width, image_words.height + image_keyboard.height),
                        self.COLOR_BACKGROUND)
        dst.paste(image_words, (int(width_diff / 2), 0))
        dst.paste(image_keyboard, (0, image_words.height))

        return convert_pil_image_to_bytes(dst)

    def generate_words(self, words: list, secret_word):
        image = Image.new("RGBA", (self.MAIN_WINDOW_WIDTH, self.MAIN_WINDOW_HEIGHT), self.COLOR_BACKGROUND)
        draw = ImageDraw.Draw(image)
        font = get_font_by_path(self.FONT_NAME, self.MAIN_WINDOW_CELL_WIDTH - 10)

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
                x2 = x1 + self.MAIN_WINDOW_CELL_WIDTH
                y2 = y1 + self.MAIN_WINDOW_CELL_HEIGHT

                color = self._get_letter_color_field(letter, secret_word, secret_word[j])

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
        font = get_font_by_path(self.FONT_NAME, self.KEYBOARD_CELL_WIDTH)

        for i, row in enumerate(layouts):

            total_width = len(row) * self.KEYBOARD_CELL_WIDTH + (len(row) - 1) * self.MAIN_WINDOW_CELL_MARGIN
            left_margin = (self.KEYBOARD_WIDTH - total_width) / 2
            for j, letter in enumerate(row):
                x1 = j * self.KEYBOARD_CELL_WIDTH + j * self.KEYBOARD_CELL_MARGIN
                y1 = i * self.KEYBOARD_CELL_HEIGHT + i * self.KEYBOARD_CELL_MARGIN
                x2 = x1 + self.KEYBOARD_CELL_WIDTH
                y2 = y1 + self.KEYBOARD_CELL_HEIGHT

                color = self._get_letter_color_keyboard(letter, exactly_correct_letters, correct_letters, wrong_letters)

                draw.rectangle((x1 + left_margin, y1, x2 + left_margin, y2), color)

                letter_width = font.getlength(letter)
                letter_margin = (self.KEYBOARD_CELL_WIDTH - letter_width) / 2
                draw.text((x1 + letter_margin + left_margin, y1 + 10), letter.upper(), font=font, fill=self.COLOR_TEXT)

        dst = Image.new('RGBA', (image.width + self.PADDING * 2, image.height + self.PADDING * 2),
                        self.COLOR_BACKGROUND)
        dst.paste(image, (self.PADDING, self.PADDING))
        return dst

    def _get_letter_color_keyboard(self, letter, exactly_correct_letters, correct_letters, wrong_letters):
        if not letter:
            return self.COLOR_DEFAULT

        if letter in exactly_correct_letters:
            return self.COLOR_CORRECT_LETTER_POS
        elif letter in correct_letters:
            return self.COLOR_CORRECT_LETTER
        elif letter in wrong_letters:
            return self.COLOR_WRONG_LETTER
        return self.COLOR_DEFAULT

    def _get_letter_color_field(self, letter, secret_word, current_secret_letter):
        if not letter:
            return self.COLOR_DEFAULT

        if letter == current_secret_letter:
            return self.COLOR_CORRECT_LETTER_POS
        elif letter in secret_word:
            return self.COLOR_CORRECT_LETTER
        elif letter not in secret_word:
            return self.COLOR_WRONG_LETTER
        return self.COLOR_DEFAULT


def send_message_session_or_edit(bot, event, session, rmi: ResponseMessageItem, max_delta):
    delta_messages = 0
    if event.message.id:
        delta_messages = event.message.id - session.message_id

    if delta_messages > max_delta:
        old_msg_id = session.message_id
        br = bot.send_response_message_item(rmi)
        message_id = br.response['result']['message_id']
        session.message_id = message_id
        session.save()
        bot.delete_messages(event.peer_id, old_msg_id)
    else:
        rmi.message_id = session.message_id
        br = bot.send_response_message_item(rmi)
    if not br.success and br.response.get('description') != \
            'Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message':
        rmi.message_id = None
        br = bot.send_response_message_item(rmi)
        message_id = br.response['result']['message_id']
        session.message_id = message_id
        session.save()
    bot.delete_messages(event.peer_id, event.message.id)
