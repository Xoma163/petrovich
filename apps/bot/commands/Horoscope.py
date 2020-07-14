from datetime import datetime

from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.commands.Meme import prepare_meme_to_send
from apps.service.models import Horoscope as HoroscopeModel

zodiac_signs = {
    "водолей": "21.01",
    "рыбы": "19.02",
    "овен": "21.03",
    "телец": "21.04",
    "близнецы": "22.05",
    "рак": "22.06",
    "лев": "23.07",
    "дева": "24.08",
    "весы": "24.09",
    "скорпион": "24.10",
    "стрелец": "23.11",
    "козерог": "22.12",
}


class Horoscope(CommonCommand):
    def __init__(self):
        names = ["гороскоп"]
        help_text = "Гороскоп - мемный гороскоп"
        detail_help_text = "Гороскоп [знак зодиака = по др в профиле] - пришлёт мемный гороскоп на день для знака зодиака\n" \
                           "Гороскоп все - пришлёт мемный гороскоп для всех знаков зодиака"
        super().__init__(names, help_text, detail_help_text, platforms=['vk', 'tg'])

    def start(self):

        if self.event.args:
            # Гороскоп для всех знаков
            if self.event.args[0] in "все":
                horoscope = HoroscopeModel.objects.first()
                for i, zodiac_sign in enumerate(zodiac_signs):
                    meme = horoscope.memes.all()[i]
                    prepared_meme = prepare_meme_to_send(self.bot, self.event, meme)
                    prepared_meme['msg'] = zodiac_sign.capitalize()
                    self.bot.parse_and_send_msgs_thread(self.event.peer_id, prepared_meme)
                return

            # Гороскоп для знака зодиака в аргументах
            try:
                zodiac_sign = self.event.args[0].lower()
                zodiac_index = list(zodiac_signs.keys()).index(zodiac_sign)
            except ValueError:
                return "Не знаю такого знака зодиака"
            return self.get_horoscope_by_zodiac(zodiac_index)

        # Гороскоп по ДР из профиля
        elif self.event.sender.birthday:
            zodiac_index = self.get_zodiac_index_of_date(self.event.sender.birthday)
            return self.get_horoscope_by_zodiac(zodiac_index)
        else:
            return "Не указана дата рождения в профиле, не могу прислать гороскоп((. \n" \
                   "Укажи знак зодиака в аргументе: /гороскоп девы"

    def get_horoscope_by_zodiac(self, zodiac_index):
        horoscope = HoroscopeModel.objects.first()
        meme = horoscope.memes.all()[zodiac_index]
        prepared_meme = prepare_meme_to_send(self.bot, self.event, meme)
        prepared_meme['msg'] = zodiac_signs[zodiac_index].capitalize()
        return prepared_meme

    @staticmethod
    def get_zodiac_index_of_date(date):
        date = date.replace(year=1900)
        zodiac_days = list(zodiac_signs.values())
        for i in range(len(zodiac_days) - 1):
            zodiac_date_start = datetime.strptime(zodiac_days[i], "%d.%m").date()
            zodiac_date_end = datetime.strptime(zodiac_days[i + 1], "%d.%m").date()
            if zodiac_date_start <= date < zodiac_date_end:
                return i
        return len(zodiac_days) - 1
