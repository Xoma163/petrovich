from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.commands.Meme import prepare_meme_to_send
from apps.service.models import Horoscope as HoroscopeModel

zodiac_signs = {
    "овен": 80,
    "телец": 111,
    "близнецы": 142,
    "рак": 173,
    "лев": 204,
    "дева": 234,
    "весы": 268,
    "скорпион": 298,
    "стрелец": 328,
    "козерог": 358,
    "водолей": 21,
    "рыбы": 51,
}

# ToDo: TG. недотестировано
class Horoscope(CommonCommand):
    def __init__(self):
        names = ["гороскоп"]
        help_text = "Гороскоп - мемный гороскоп"
        detail_help_text = "Гороскоп [знак зодиака = по др в профиле] - пришлёт мемный гороскоп на день для знака зодиака\n" \
                           "Гороскоп все - пришлёт мемный гороскоп для всех знаков зодиака"
        super().__init__(names, help_text, detail_help_text, api=False)

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
            return self.get_horoscope_by_zodiac(zodiac_sign, zodiac_index)

        # Гороскоп по ДР из профиля
        elif self.event.sender.birthday:
            zodiac_sign, zodiac_index = self.get_zodiac_of_date(self.event.sender.birthday)
            return self.get_horoscope_by_zodiac(zodiac_sign, zodiac_index)
        else:
            return "Не указана дата рождения в профиле, не могу прислать гороскоп((. \n" \
                   "Укажи знак зодиака в аргументе: /гороскоп девы"

    def get_horoscope_by_zodiac(self, zodiac_sign, zodiac_index):
        horoscope = HoroscopeModel.objects.first()
        if not horoscope:
            raise RuntimeWarning('На сегодня гороскопа нет')
        meme = horoscope.memes.all()[zodiac_index]
        prepared_meme = prepare_meme_to_send(self.bot, self.event, meme)
        prepared_meme['msg'] = zodiac_sign.capitalize()
        return prepared_meme

    def get_zodiac_of_date(self, date):
        day_number = int(date.strftime("%j"))
        deltas = []
        min_delta = 999
        min_delta_index = 0
        for i, zodiac in enumerate(zodiac_signs):
            delta = day_number - zodiac_signs[zodiac]
            if delta >= 0:
                if delta < min_delta:
                    min_delta = delta
                    min_delta_index = i
            deltas.append(day_number - zodiac_signs[zodiac])
        return list(zodiac_signs.keys())[min_delta_index], min_delta_index
