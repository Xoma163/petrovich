import json
from threading import Lock

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform, Role
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.utils import random_event, get_tg_italic_text, get_tg_underline_text, get_tg_bold_text
from apps.games.models import Wordle as WordleModel

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
    help_texts_extra = "Нижнее подчёркивание означает, что буква стоит на месте, курсив+жир = буква присутствует в слове"

    platforms = [Platform.TG]
    access = Role.GAMER

    MAX_STEPS = 6
    WORDLE_WORDS_PATH = "static/bot/games/wordle/wordle.json"

    def start(self):
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
        return method()

    def start_session(self):
        existed_session = self.get_session()
        if existed_session:
            raise PWarning("Игра уже начата")

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

        return "Игра начата. Поехали!"

    def hypothesis(self):
        hypothesis = self.event.message.args[0]
        session = self.get_session()
        if not session:
            b = self.bot.get_button("Начать", "wordle")
            kb = self.bot.get_inline_keyboard([b])
            raise PWarning("Игра не начата! Начните её", keyboard=kb)

        if len(hypothesis) != 5:
            return PWarning("Слово должно состоять из 5 букв")

        if hypothesis == session.word:
            return self.win()

        session.hypotheses.append(hypothesis)
        session.steps += 1
        session.save()

        if len(session.hypotheses) > 5:
            msgs = [self.get_answer_for_user_if_wrong(session), self.lose()]
            return msgs

        return self.get_answer_for_user_if_wrong(session)

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
        for i, letter in enumerate(hypothesis):
            for j, letter2 in enumerate(answer):
                if letter == letter2:
                    if i == j:
                        exactly_correct_letters.append(i)
                    else:
                        correct_letters.append(i)
        return correct_letters, exactly_correct_letters

    def get_answer_for_user_if_wrong(self, session) -> str:
        text = []
        for hypothesis in session.hypotheses:
            correct_letters, exactly_correct_letters = self.calculate_words(hypothesis, session.word)
            text_line = ""
            for i, word in enumerate(hypothesis):
                if i in correct_letters:
                    text_line += get_tg_bold_text(get_tg_italic_text(word))
                elif i in exactly_correct_letters:
                    text_line += get_tg_underline_text(word)
                else:
                    text_line += f"{word}"
                text_line += " "
            text_line = text_line.rstrip()
            text.append(text_line)

        return "\n".join(text)

    def win(self):
        session = self.get_session()
        word = session.word
        session.delete()
        return f"Вы победили! Загаданное слово - {word}"

    def lose(self):
        session = self.get_session()
        word = session.word
        session.delete()
        return f"Загаданное слово - {word}"
