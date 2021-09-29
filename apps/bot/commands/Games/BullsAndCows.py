import random
from threading import Lock

from apps.bot.classes.Consts import Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import decl_of_num
from apps.games.models import BullsAndCowsSession

lock = Lock()

DIGITS_IN_GAME = 4


class BullsAndCows(CommonCommand):
    name = "бк"
    names = ["бик", "быкиикоровы"]
    help_text = "быки и коровы. Игра, где нужно угадать загаданное число."
    help_texts = [
        "- создаёт новую игру",
        "[число] - проверяет гипотезу",
        "сдаться - закончить игру",
    ]

    platforms = [Platform.VK, Platform.TG]

    def start(self):
        with lock:
            if self.event.chat:
                session = BullsAndCowsSession.objects.get(chat=self.event.chat).first()
            else:
                session = BullsAndCowsSession.objects.filter(author=self.event.sender).first()

            if not self.event.args:
                if session:
                    return f"Игра уже создана, присылай мне число из {DIGITS_IN_GAME} цифр"
                digits = [str(x) for x in range(10)]
                random.shuffle(digits)
                new_obj = {
                    'number': "".join(digits[:DIGITS_IN_GAME])
                }
                if self.event.from_chat:
                    new_obj['chat'] = self.event.chat
                else:
                    new_obj['author'] = self.event.sender
                BullsAndCowsSession.objects.create(**new_obj)
                print(new_obj['number'])
                return "Я создал, погнали!"
            else:

                if not session:
                    raise PWarning("Нет созданной игры. Начни её - /бк")

                arg0 = self.event.args[0]
                if arg0 in ['сдаться', 'сдаюсь', 'ойвсё', 'пощади', 'надоело']:
                    session.delete()
                    return "В следующий раз повезёт :("

                if len(arg0) != DIGITS_IN_GAME:
                    raise PWarning(f"В отгадываемом числе должно быть {DIGITS_IN_GAME} цифр")
                self.int_args = [0]
                self.parse_int()

                if arg0 != ''.join(sorted(set(arg0), key=arg0.index)):
                    raise PWarning("Цифры должны быть уникальны в числе")

                if self.event.args[0] == session.number:
                    decl = decl_of_num(session.steps, ['попытку', 'попытки', 'попыток'])
                    msg = f"Отгадали всего за {session.steps} {decl}!"
                    session.delete()
                    keyboard = self.bot.get_inline_keyboard(self.name, "Ещё")
                    return {"msg": msg, "keyboard": keyboard}

                bulls = 0
                cows = 0
                correct_number_str = str(session.number)
                for i in range(len(arg0)):
                    if arg0[i] == correct_number_str[i]:
                        bulls += 1
                    elif arg0[i] in correct_number_str:
                        cows += 1
                session.steps += 1
                session.save()
                return f"Число {arg0}\nБыков - {bulls}\nКоров - {cows}"
