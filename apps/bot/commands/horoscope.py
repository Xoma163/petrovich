from datetime import datetime
from time import sleep

from apps.bot.classes.command import Command
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.commands.meme import Meme
from apps.service.models import Horoscope as HoroscopeModel


class ZodiacSign:
    def __init__(self, name, signs, start_date):
        self.name = name
        self.signs = signs
        self.start_date = start_date

    def is_contains_name_or_sign(self, text):
        if text in self.name or text in self.signs:
            return True


class ZodiacSigns:
    def __init__(self, signs: list):
        self.signs = signs

    def find_zodiac_sign_by_date(self, date):
        date = date.replace(year=1900)
        zodiac_days = [x.start_date for x in self.signs]
        for i in range(len(zodiac_days) - 1):
            zodiac_date_start = datetime.strptime(zodiac_days[i], "%d.%m").date()
            zodiac_date_end = datetime.strptime(zodiac_days[i + 1], "%d.%m").date()
            if zodiac_date_start <= date < zodiac_date_end:
                return self.signs[i]
        return self.signs[-1]

    def get_zodiac_sign_index(self, zodiac_sign: ZodiacSign):
        for i, _zodiac_sign in enumerate(self.signs):
            if zodiac_sign == _zodiac_sign:
                return i

    def get_zodiac_sign_by_sign_or_name(self, text):
        for zodiac_sign in self.signs:
            if zodiac_sign.is_contains_name_or_sign(text):
                return zodiac_sign
        raise PWarning("Не знаю такого знака зодиака")

    def get_zodiac_signs(self):
        return self.signs


class Horoscope(Command):
    name = "гороскоп"
    name_tg = "horoscope"

    help_text = "мемный гороскоп"
    help_texts = [
        "[знак зодиака = по др в профиле] - пришлёт мемный гороскоп на день для знака зодиака",
        "все - пришлёт мемный гороскоп для всех знаков зодиака",
        "инфо (знак зодиака) - пришлёт информацию о мемасе в гороскопе по знаку зодиака",
        "конфа - пришлёт гороскоп для всех участников конфы"
    ]
    zodiac_signs = ZodiacSigns([
        ZodiacSign("водолей", ['♒', "♒️"], "21.01"),
        ZodiacSign("рыбы", ["♓", "♓️"], "19.02"),
        ZodiacSign("овен", ["♈", "♈️"], "21.03"),
        ZodiacSign("телец", ["♉", "♉️"], "21.04"),
        ZodiacSign("близнецы", ["♊", "♊️"], "22.05"),
        ZodiacSign("рак", ["♋", "♋️"], "22.06"),
        ZodiacSign("лев", ["♌", "♌️"], "23.07"),
        ZodiacSign("дева", ["♍", "♍️"], "24.08"),
        ZodiacSign("весы", ["♎", "♎️"], "24.09"),
        ZodiacSign("скорпион", ["♏", "♏️"], "24.10"),
        ZodiacSign("стрелец", ["♐", "♐️"], "23.11"),
        ZodiacSign("козерог", ["♑", "♑️"], "22.12"),
    ])

    def start(self) -> ResponseMessage:
        if self.event.message.args:
            # Гороскоп для всех знаков
            if self.event.message.args[0] in "все":
                return self.get_horoscope_for_all()
            elif self.event.message.args[0] in "инфо":
                return self.get_horoscope_info()
            elif self.event.message.args[0] in "конфа":
                return self.get_horoscope_for_conference()
            # Гороскоп для знака зодиака в аргументах
            zodiac_sign_name = self.event.message.args[0]
            zodiac_sign = self.zodiac_signs.get_zodiac_sign_by_sign_or_name(zodiac_sign_name)
            horoscope = self.get_horoscope_by_zodiac_sign(zodiac_sign)
            horoscope_with_button = self.get_horoscope_hint_msg(horoscope)
            return horoscope_with_button

        # Гороскоп по ДР из профиля
        elif self.event.sender.birthday:
            zodiac_sign = self.zodiac_signs.find_zodiac_sign_by_date(self.event.sender.birthday)
            horoscope = self.get_horoscope_by_zodiac_sign(zodiac_sign)
            horoscope_with_button = self.get_horoscope_hint_msg(horoscope)
            return horoscope_with_button
        else:
            raise PWarning(
                "Не указана дата рождения в профиле, не могу прислать гороскоп\n"
                f"Укажи знак зодиака в аргументе: {self.bot.get_formatted_text_line('/гороскоп дева')}\n"
                f"Или укажите дату рождения в профиле: {self.bot.get_formatted_text_line('/профиль др ДД.ММ.ГГГГ')}"
            )

    def get_horoscope_for_all(self):
        horoscope = HoroscopeModel.objects.first()
        self.check_horoscope(horoscope)
        signs = self.zodiac_signs.get_zodiac_signs()
        for sign in signs:
            message = self.get_horoscope_by_zodiac_sign(sign)
            message.peer_id = self.event.peer_id
            message.message_thread_id = self.event.message_thread_id
            self.bot.send_response_message_thread(ResponseMessage(message))
            sleep(1)

    def get_horoscope_for_conference(self):
        self.check_conversation()
        chat_users = self.event.chat.users.all()
        signs = []
        for user in chat_users:
            if not user.birthday:
                continue
            sign = self.zodiac_signs.find_zodiac_sign_by_date(user.birthday)
            if sign not in signs:
                signs.append(sign)
        if not signs:
            raise PWarning(
                "Ни у кого в конфе не проставлено ДР\n"
                f"Укажите дату рождения в профиле: {self.bot.get_formatted_text_line('/профиль др ДД.ММ.ГГГГ')}"
            )
        for sign in signs:
            message = self.get_horoscope_by_zodiac_sign(sign)
            message.peer_id = self.event.peer_id
            message.message_thread_id = self.event.message_thread_id
            self.bot.send_response_message_thread(ResponseMessage(message))
            sleep(1)

    def get_horoscope_info(self) -> ResponseMessage:
        self.check_args(2)
        try:
            zodiac_sign_name = self.event.message.args[1]
            zodiac_sign = self.zodiac_signs.get_zodiac_sign_by_sign_or_name(zodiac_sign_name)
            zodiac_sign_index = self.zodiac_signs.get_zodiac_sign_index(zodiac_sign)
        except Exception:
            raise PWarning("Не знаю такого знака зодиака")
        horoscope = HoroscopeModel.objects.first()
        self.check_horoscope(horoscope)
        meme = horoscope.memes.all()[zodiac_sign_index]
        answer = f"{zodiac_sign.name.capitalize()}\n{meme.get_info()}"
        return ResponseMessage(ResponseMessageItem(text=answer))

    def get_horoscope_by_zodiac_sign(self, zodiac_sign) -> ResponseMessageItem:
        horoscope = HoroscopeModel.objects.first()
        self.check_horoscope(horoscope)
        zodiac_sign_index = self.zodiac_signs.get_zodiac_sign_index(zodiac_sign)
        zodiac_sign_name = zodiac_sign.name.capitalize()
        meme = horoscope.memes.all()[zodiac_sign_index]

        meme_command = Meme(bot=self.bot, event=self.event)
        prepared_meme = meme_command.prepare_meme_to_send(meme)
        if prepared_meme.text:
            prepared_meme.text = f"{zodiac_sign_name}\n{prepared_meme.text}"
        else:
            prepared_meme.text = zodiac_sign_name
        return prepared_meme

    def get_horoscope_hint_msg(self, rmi: ResponseMessageItem = None) -> ResponseMessage:
        if not rmi:
            rmi = ResponseMessageItem(text="Узнать мой гороскоп")
        button = self.bot.get_button(self.name.capitalize(), self.name)
        rmi.keyboard = self.bot.get_inline_keyboard([button])
        return ResponseMessage(rmi)

    @staticmethod
    def check_horoscope(horoscope: HoroscopeModel):
        if not horoscope:
            raise PWarning("На сегодня ещё нет гороскопа")
