import random

from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role, Platform
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.utils.utils import decl_of_num, send_message_session_or_edit
from apps.games.models import BullsAndCowsSession


class BullsAndCows(Command):
    name = "бк"
    names = ["бик", "быкиикоровы", "быки", "коровы"]

    help_text = HelpText(
        commands_text="быки и коровы. Игра, где нужно угадать загаданное число.",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand(None, "создаёт новую игру"),
                HelpTextItemCommand("[число]", "проверяет гипотезу"),
                HelpTextItemCommand("сдаться", "закончить игру"),
            ])
        ]
    )

    DIGITS_IN_GAME = 4

    def start(self) -> ResponseMessage:
        if self.event.chat:
            session = BullsAndCowsSession.objects.filter(chat=self.event.chat).first()
        else:
            session = BullsAndCowsSession.objects.filter(profile=self.event.sender).first()

        if not self.event.message.args:
            return self.start_game(session)
        else:
            return self.play_game(session)

    def start_game(self, session) -> ResponseMessage:
        if session:
            return self._send_message(session)

        new_obj = {
            'number': self.get_random_number()
        }
        if self.event.is_from_chat:
            new_obj['chat'] = self.event.chat
        else:
            new_obj['profile'] = self.event.sender
        bacs = BullsAndCowsSession.objects.create(**new_obj)

        rmi = ResponseMessageItem(
            text="Я создал, погнали",
            peer_id=self.event.peer_id,
            message_thread_id=self.event.message_thread_id
        )
        if self.event.platform == Platform.TG:
            br = self.bot.send_response_message_item(rmi)
            message_id = br.response['result']['message_id']
            bacs.message_body = rmi.text
            bacs.message_id = message_id
            bacs.save()
            return ResponseMessage(rmi, send=False)
        return ResponseMessage(rmi)

    def get_random_number(self):
        digits = [str(x) for x in range(10)]
        random.shuffle(digits)
        return "".join(digits[:self.DIGITS_IN_GAME])

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
            correct_number_str = "0" * (self.DIGITS_IN_GAME - len(correct_number_str)) + correct_number_str
            session.delete()

            answer = f"В следующий раз повезёт :(\nЗагаданное число - {correct_number_str}"
            return ResponseMessage(ResponseMessageItem(text=answer))

        if len(arg0) != self.DIGITS_IN_GAME:
            decl = decl_of_num(self.DIGITS_IN_GAME, ['цифра', 'цифры', 'цифр'])
            raise PWarning(f"В отгадываемом числе должно быть {self.DIGITS_IN_GAME} {decl}")

        self.int_args = [0]
        self.parse_int()

        if arg0 != ''.join(sorted(set(arg0), key=arg0.index)):
            raise PWarning("Цифры должны быть уникальны в числе")

        if self.event.message.args[0] == session.number:
            if self.event.platform == Platform.TG:
                self.bot.delete_messages(self.event.peer_id, self.event.message.id)
            decl = decl_of_num(session.steps, ['попытку', 'попытки', 'попыток'])
            gamer = self.event.sender.gamer
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
        correct_number_str = "0" * (self.DIGITS_IN_GAME - len(correct_number_str)) + correct_number_str
        for i, argi in enumerate(arg0):
            if argi == correct_number_str[i]:
                bulls += 1
            elif argi in correct_number_str:
                cows += 1
        session.steps += 1
        new_msg = f"Число {arg0}\nБыков - {bulls}\nКоров - {cows}"
        session.message_body += f"\n\n{new_msg}"
        session.save()

        return self._send_message(session)

    def _send_message(self, session) -> ResponseMessage:
        message_without_duplications = "\n\n".join(list(dict.fromkeys(session.message_body.split('\n\n'))))
        rmi = ResponseMessageItem(
            text=message_without_duplications,
            peer_id=self.event.peer_id,
            message_thread_id=self.event.message_thread_id
        )
        send_message_session_or_edit(self.bot, self.event, session, rmi, 8)
        return ResponseMessage(rmi, send=False)
