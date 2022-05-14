import random
from threading import Lock

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.utils import decl_of_num
from apps.games.models import BullsAndCowsSession

lock = Lock()

DIGITS_IN_GAME = 4


class BullsAndCows(Command):
    name = "бк"
    names = ["бик", "быкиикоровы", "быки", "коровы"]
    help_text = "быки и коровы. Игра, где нужно угадать загаданное число."
    help_texts = [
        "- создаёт новую игру",
        "[число] - проверяет гипотезу",
        "сдаться - закончить игру",
    ]
    access = Role.GAMER

    def start(self):
        with lock:
            if self.event.chat:
                session = BullsAndCowsSession.objects.filter(chat=self.event.chat).first()
            else:
                session = BullsAndCowsSession.objects.filter(profile=self.event.sender).first()
            if not self.event.message.args:
                if session:
                    return f"Игра уже создана, присылай мне число из {DIGITS_IN_GAME} цифр"
                digits = [str(x) for x in range(10)]
                random.shuffle(digits)
                new_obj = {
                    'number': "".join(digits[:DIGITS_IN_GAME])
                }
                if self.event.is_from_chat:
                    new_obj['chat'] = self.event.chat
                else:
                    new_obj['profile'] = self.event.sender
                BullsAndCowsSession.objects.create(**new_obj)
                return "Я создал, погнали!"
            else:

                if not session:
                    raise PWarning("Нет созданной игры. Начни её - /бк")

                arg0 = self.event.message.args[0]
                if arg0 in ['сдаться', 'сдаюсь', 'ойвсё', 'пощади', 'надоело']:
                    correct_number_str = str(session.number)
                    correct_number_str = "0" * (DIGITS_IN_GAME - len(correct_number_str)) + correct_number_str
                    session.delete()
                    return f"В следующий раз повезёт :(\nЗагаданное число - {correct_number_str}"

                if len(arg0) != DIGITS_IN_GAME:
                    raise PWarning(f"В отгадываемом числе должно быть {DIGITS_IN_GAME} цифр")
                self.int_args = [0]
                self.parse_int()

                if arg0 != ''.join(sorted(set(arg0), key=arg0.index)):
                    raise PWarning("Цифры должны быть уникальны в числе")

                if self.event.message.args[0] == session.number:
                    decl = decl_of_num(session.steps, ['попытку', 'попытки', 'попыток'])
                    msg = f"Отгадали всего за {session.steps} {decl}!"
                    msg2 = "Начислил 1000 очков"
                    session.delete()
                    button = self.bot.get_button("Ещё", self.name)
                    keyboard = self.bot.get_inline_keyboard([button])
                    return [{"text": msg, "keyboard": keyboard}, msg2]

                bulls = 0
                cows = 0
                correct_number_str = str(session.number)
                # Добиваем нулями если число начинается с нулей
                correct_number_str = "0" * (DIGITS_IN_GAME - len(correct_number_str)) + correct_number_str
                for i, argi in enumerate(arg0):
                    if argi == correct_number_str[i]:
                        bulls += 1
                    elif argi in correct_number_str:
                        cows += 1
                session.steps += 1
                session.save()
                return f"Число {arg0}\nБыков - {bulls}\nКоров - {cows}"
