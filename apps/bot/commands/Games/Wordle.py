import json
from threading import Lock

from apps.bot.classes.Command import Command
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.consts.Consts import Platform, Role, rus_alphabet
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.utils import random_event
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
    help_texts_extra = "[] означает, что буква стоит на месте\n() означает, что буква присутствует в слове"

    platforms = [Platform.TG]
    access = Role.GAMER

    bot: TgBot

    MAX_STEPS = 6
    WORDLE_WORDS_PATH = "static/bot/games/wordle/wordle.json"

    # ToDo: self.session
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
            return self.get_current_state(existed_session)

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

        hypothesis = "".join([x for x in hypothesis if x.isalpha() and x in rus_alphabet])
        if len(hypothesis) != 5:
            raise PWarning("Слово должно состоять из 5 букв")

        if hypothesis == session.word:
            return self.win()

        session.hypotheses.append(hypothesis)
        session.steps += 1
        session.save()

        if len(session.hypotheses) > 5:
            msgs = [self.get_answer_for_user_if_wrong(session), self.lose()]
            return msgs

        return self.get_current_state(session)

    def get_current_state(self, session):
        msg = self.get_answer_for_user_if_wrong(session)
        msg += f"\n\n{self.get_text_keyboard(session)}"
        if self.event.platform == Platform.TG:
            delta_messages = self.event.message.id - session.message_id
            if delta_messages > 8:
                old_msg_id = session.message_id
                r = self.bot.parse_and_send_msgs(msg, self.event.peer_id, self.event.message_thread_id)[0]
                message_id = r['response'].json()['result']['message_id']
                session.message_id = message_id
                session.save()
                self.bot.delete_message(self.event.peer_id, old_msg_id)
            else:
                r = self.bot.parse_and_send_msgs({
                    'text': msg,
                    'message_id': session.message_id},
                    self.event.peer_id,
                    self.event.message_thread_id
                )[0]
            if not r['success']:
                r = self.bot.parse_and_send_msgs({'text': msg}, self.event.peer_id, self.event.message_thread_id)[0]
                message_id = r['response'].json()['result']['message_id']
                session.message_id = message_id
                session.save()
            self.bot.delete_message(self.event.peer_id, self.event.message.id)
        else:
            return msg

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

    def get_answer_for_user_if_wrong(self, session) -> str:
        text = []
        for hypothesis in session.hypotheses:
            correct_letters, exactly_correct_letters, _ = self.calculate_words(hypothesis, session.word)
            text_line = ""
            for i, word in enumerate(hypothesis):
                if i in exactly_correct_letters:
                    text_line += f"[{word}]"
                elif i in correct_letters:
                    text_line += f"({word})"
                else:
                    text_line += f"{word}"
                text_line += " "
            text_line = text_line.rstrip()
            text.append(text_line)

        return "\n".join(text)

    def get_text_keyboard(self, session):
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

        layouts = [
            ["й", "ц", "у", "к", "е", "н", "г", "ш", "щ", "з", "х", "ъ"],
            ["ф", "ы", "в", "а", "п", "р", "о", "л", "д", "ж", "э"],
            ["я", "ч", "с", "м", "и", "т", "ь", "б", "ю"]
        ]

        for i, layer in enumerate(layouts):
            for j, word in enumerate(layer):
                if word in exactly_correct_letters:
                    layouts[i][j] = f"[{word}]"
                if word in correct_letters:
                    layouts[i][j] = f"({word})"
                if word in wrong_letters:
                    layouts[i][j] = ""
            layouts[i] = list(filter(lambda x: x, layouts[i]))
        layouts_list = [" ".join(x) for x in layouts]
        kb_txt = "\n".join(layouts_list)
        return kb_txt

    def win(self):
        session = self.get_session()
        word = session.word
        session.delete()
        gamer = self.bot.get_gamer_by_profile(self.event.sender)
        gamer.roulette_points += 1000
        gamer.wordle_points += 1
        gamer.save()
        text = f"Вы победили! Загаданное слово - {word}\n" \
               f"Начислил 1000 очков рулетки"
        button = self.bot.get_button("Ещё", self.name)
        keyboard = self.bot.get_inline_keyboard([button])
        return {"text": text, "keyboard": keyboard}

    def lose(self):
        session = self.get_session()
        word = session.word
        session.delete()
        text = f"Загаданное слово - {word}"
        button = self.bot.get_button("Ещё", self.name)
        keyboard = self.bot.get_inline_keyboard([button])
        return {"text": text, "keyboard": keyboard}
