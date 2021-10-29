from datetime import datetime

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.commands.Meme import Meme
from apps.service.models import Horoscope as HoroscopeModel


class Horoscope(Command):
    name = "гороскоп"
    help_text = "мемный гороскоп"
    help_texts = [
        "[знак зодиака = по др в профиле] - пришлёт мемный гороскоп на день для знака зодиака",
        "все - пришлёт мемный гороскоп для всех знаков зодиака",
        "инфо (знак зодиака) - пришлёт информацию о мемасе в гороскопе по знаку зодиака",
        "конфа - пришлёт гороскоп для всех участников конфы"
    ]

    def __init__(self):
        super().__init__()

        self.zodiac_signs = ZodiacSigns([
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

    def start(self):
        if self.event.message.args:
            # Гороскоп для всех знаков
            if self.event.message.args[0] in "все":
                horoscope = HoroscopeModel.objects.first()
                if not horoscope:
                    raise PWarning("На сегодня ещё нет гороскопа")
                for i, zodiac_sign in enumerate(self.zodiac_signs.get_zodiac_signs()):
                    meme = horoscope.memes.all()[i]
                    zodiac_sign_name = zodiac_sign.name.capitalize()
                    try:
                        meme_command = Meme(bot=self.bot)
                        prepared_meme = meme_command.prepare_meme_to_send(meme)
                    except PWarning as e:
                        error_msg = f"{zodiac_sign_name}\n{str(e)}"
                        self.bot.parse_and_send_msgs_thread(self.event.peer_id, error_msg)
                        continue
                    if prepared_meme.get('text', None):
                        prepared_meme['text'] = f"{zodiac_sign_name}\n{prepared_meme['text']}"
                    else:
                        prepared_meme['text'] = zodiac_sign_name
                    self.bot.parse_and_send_msgs_thread(self.event.peer_id, prepared_meme)
                return
            elif self.event.message.args[0] in "инфо":
                self.check_args(2)
                try:
                    zodiac_sign_name = self.event.message.args[1]
                    zodiac_sign = self.zodiac_signs.get_zodiac_sign_by_sign_or_name(zodiac_sign_name)
                    zodiac_sign_index = self.zodiac_signs.get_zodiac_sign_index(zodiac_sign)
                except Exception:
                    raise PWarning("Не знаю такого знака зодиака")
                horoscope = HoroscopeModel.objects.first()
                if not horoscope:
                    raise PWarning("На сегодня ещё нет гороскопа")
                meme = horoscope.memes.all()[zodiac_sign_index]
                return f"{zodiac_sign.name.capitalize()}\n{meme.get_info()}"
            elif self.event.message.args[0] in "конфа":
                self.check_conversation()
                chat_users = self.event.chat.users.all()
                all_zodiac_signs = set(
                    self.zodiac_signs.find_zodiac_sign_by_date(x.birthday) for x in chat_users if x.birthday)
                messages = []
                for zodiac_sign in all_zodiac_signs:
                    messages.append(self.get_horoscope_by_zodiac_sign(zodiac_sign))
                return messages
            # Гороскоп для знака зодиака в аргументах
            zodiac_sign_name = self.event.message.args[0]
            zodiac_sign = self.zodiac_signs.get_zodiac_sign_by_sign_or_name(zodiac_sign_name)
            return self.get_horoscope_by_zodiac_sign(zodiac_sign)

        # Гороскоп по ДР из профиля
        elif self.event.sender.birthday:
            zodiac_sign = self.zodiac_signs.find_zodiac_sign_by_date(self.event.sender.birthday)
            return self.get_horoscope_by_zodiac_sign(zodiac_sign)
        else:
            raise PWarning("Не указана дата рождения в профиле, не могу прислать гороскоп((. \n"
                           "Укажи знак зодиака в аргументе: /гороскоп дева")

    def get_horoscope_by_zodiac_sign(self, zodiac_sign):
        horoscope = HoroscopeModel.objects.first()
        if not horoscope:
            raise PWarning("На сегодня ещё нет гороскопа")
        zodiac_sign_index = self.zodiac_signs.get_zodiac_sign_index(zodiac_sign)
        zodiac_sign_name = zodiac_sign.name.capitalize()
        meme = horoscope.memes.all()[zodiac_sign_index]

        meme_command = Meme(bot=self.bot)
        prepared_meme = meme_command.prepare_meme_to_send(meme)
        if prepared_meme.get('text', None):
            prepared_meme['text'] = f"{zodiac_sign_name}\n{prepared_meme['text']}"
        else:
            prepared_meme['text'] = zodiac_sign_name
        prepared_meme['keyboard'] = self.bot.get_inline_keyboard(
            [{'command': self.name, 'button_text': self.name.capitalize()}])
        return prepared_meme


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
