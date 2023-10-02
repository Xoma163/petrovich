import random
from threading import Lock
from typing import Optional

from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role, Platform
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.utils.utils import decl_of_num, _send_message_session_or_edit
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

    def start(self) -> ResponseMessage:
        with lock:
            if self.event.chat:
                session = BullsAndCowsSession.objects.filter(chat=self.event.chat).first()
            else:
                session = BullsAndCowsSession.objects.filter(profile=self.event.sender).first()
            if not self.event.message.args:
                return self.start_game(session)
            else:
                return self.play_game(session)

    def start_game(self, session) -> Optional[ResponseMessage]:
        if session:
            raise PWarning(f"Игра уже создана, присылай мне число из {DIGITS_IN_GAME} цифр")
        digits = [str(x) for x in range(10)]
        random.shuffle(digits)
        new_obj = {
            'number': "".join(digits[:DIGITS_IN_GAME]),
        }
        if self.event.is_from_chat:
            new_obj['chat'] = self.event.chat
        else:
            new_obj['profile'] = self.event.sender
        bacs = BullsAndCowsSession.objects.create(**new_obj)

        answer = "Я создал, погнали"
        if self.event.platform == Platform.TG:
            rmi = ResponseMessageItem(text=answer, peer_id=self.event.peer_id,
                                      message_thread_id=self.event.message_thread_id)
            br = self.bot.send_response_message_item(rmi)
            message_id = br.response['result']['message_id']
            bacs.message_body = "Я создал, погнали"
            bacs.message_id = message_id
            bacs.save()
            return
        return ResponseMessage(ResponseMessageItem(text=answer))

    def play_game(self, session) -> ResponseMessage:
        if not session:
            button = self.bot.get_button('Начать игру', self.name)
            keyboard = self.bot.get_inline_keyboard([button])
            raise PWarning(
                f"Нет созданной игры. Начни её - {self.bot.get_formatted_text_line('/бк')}",
                keyboard=keyboard
            )

        arg0 = self.event.message.args[0]
        if arg0 in ['сдаться', 'сдаюсь', 'ойвсё', 'пощади', 'надоело']:
            correct_number_str = str(session.number)
            correct_number_str = "0" * (DIGITS_IN_GAME - len(correct_number_str)) + correct_number_str
            session.delete()

            answer = f"В следующий раз повезёт :(\nЗагаданное число - {correct_number_str}"
            return ResponseMessage(ResponseMessageItem(text=answer))

        if len(arg0) != DIGITS_IN_GAME:
            raise PWarning(f"В отгадываемом числе должно быть {DIGITS_IN_GAME} цифр")
        self.int_args = [0]
        self.parse_int()

        if arg0 != ''.join(sorted(set(arg0), key=arg0.index)):
            raise PWarning("Цифры должны быть уникальны в числе")

        if self.event.message.args[0] == session.number:
            if self.event.platform == Platform.TG:
                self.bot.delete_message(self.event.peer_id, self.event.message.id)
            decl = decl_of_num(session.steps, ['попытку', 'попытки', 'попыток'])
            gamer = self.bot.get_gamer_by_profile(self.event.sender)
            gamer.roulette_points += 1000
            gamer.bk_points += 1
            gamer.save()
            answer = f"Отгадали число {session.number} всего за {session.steps} {decl}!\n" \
                     f"Начислил 1000 очков рулетки"
            session.delete()
            button = self.bot.get_button("Ещё", self.name)
            keyboard = self.bot.get_inline_keyboard([button])

            return ResponseMessage(ResponseMessageItem(text=answer, keyboard=keyboard))

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
        new_msg = f"Число {arg0}\nБыков - {bulls}\nКоров - {cows}"
        session.message_body += f"\n\n{new_msg}"
        session.save()

        message_without_duplications = "\n\n".join(list(dict.fromkeys(session.message_body.split('\n\n'))))
        rmi = ResponseMessageItem(text=message_without_duplications, peer_id=self.event.peer_id,
                                  message_thread_id=self.event.message_thread_id)
        _send_message_session_or_edit(self.bot, self.event, session, rmi, 8)
