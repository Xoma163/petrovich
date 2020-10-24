from datetime import datetime

from apps.bot.APIs.TimezoneDBAPI import TimezoneDBAPI
from apps.bot.APIs.YandexGeoAPI import YandexGeoAPI
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.service.models import City, TimeZone


class Profile(CommonCommand):
    def __init__(self):
        names = ["профиль"]
        help_text = "Профиль - позволяет управлять вашим профилем"
        detail_help_text = "Профиль - присылает информацию по вашему профилю.\n" \
                           "Профиль город (название города) - устанавливает новый город\n" \
                           "Профиль город добавить (название города) - добавляет новый город в базу\n" \
                           "Профиль др (дата) - устанавливает новый др\n" \
                           "Профиль никнейм (никнейм) - устанавливает новый никнейм\n" \
                           "Профиль пол (мужской/женский) - устанавливает новый пол"

        super().__init__(names, help_text, detail_help_text)

    def start(self):
        if not self.event.args:
            _city = self.event.sender.city or "Не установлено"
            _bd = self.event.sender.birthday
            if _bd:
                _bd = _bd.strftime('%d.%m.%Y')
            else:
                _bd = "Не установлено"
            _nickname = self.event.sender.nickname_real or "Не установлено"
            msg = f"Город - {_city}\n" \
                  f"Дата рождения - {_bd}\n" \
                  f"Никнейм - {_nickname}\n" \
                  f"Пол - {self.event.sender.get_gender_display()}"
            return msg
        else:
            self.check_args(2)
            arg0 = self.event.args[0].lower()

            menu = [
                [["город"], self.menu_city],
                [["др"], self.menu_bd],
                [['ник', 'никнейм'], self.menu_nickname],
                [['пол'], self.menu_gender],
            ]
            method = self.handle_menu(menu, arg0)
            return method()

    def menu_city(self):
        arg1 = self.event.args[1]
        if arg1 == 'добавить':
            city_name = " ".join(self.event.args[2:])
            city = add_city_to_db(city_name)
            return f"Добавил новый город - {city.name}"
        else:
            city_name = " ".join(self.event.args[1:])
            city = City.objects.filter(synonyms__icontains=city_name).first()
            if not city:
                raise RuntimeWarning("Не нашёл такого города. /профиль город добавить (название)")
            self.event.sender.city = city
            self.event.sender.save()
            return f"Изменил город на {self.event.sender.city.name}"

    def menu_bd(self):
        birthday = self.event.args[1]
        date_time_obj = datetime.strptime(birthday, '%d.%m.%Y')
        self.event.sender.birthday = date_time_obj.date()
        self.event.sender.save()
        return f"Изменил дату рождения на {self.event.sender.birthday.strftime('%d.%m.%Y')}"

    def menu_nickname(self):
        nickname = " ".join(self.event.args[1:])
        self.event.sender.nickname_real = nickname
        self.event.sender.save()
        return f"Изменил никнейм на {self.event.sender.nickname_real}"

    def menu_gender(self):
        gender = self.event.args[1]
        if gender == 'мужской':
            gender_code = self.event.sender.GENDER_MALE
        elif gender == 'женский':
            gender_code = self.event.sender.GENDER_FEMALE
        else:
            gender_code = self.event.sender.GENDER_NONE
        self.event.sender.gender = gender_code
        self.event.sender.save()
        return f"Изменил пол на {self.event.sender.get_gender_display()}"


def add_city_to_db(city_name):
    yandexgeo_api = YandexGeoAPI()
    city_info = yandexgeo_api.get_city_info_by_name(city_name)
    if not city_info:
        raise RuntimeWarning("Не смог найти координаты для города")
    city = City.objects.filter(name=city_info['name'])
    if len(city) != 0:
        raise RuntimeWarning("Такой город уже есть")
    city_info['synonyms'] = city_info['name'].lower()
    timezonedb_api = TimezoneDBAPI()
    timezone_name = timezonedb_api.get_timezone_by_coordinates(city_info['lat'], city_info['lon'])
    if not timezone_name:
        raise RuntimeWarning("Не смог найти таймзону для города")
    timezone_obj, _ = TimeZone.objects.get_or_create(name=timezone_name)

    city_info['timezone'] = timezone_obj
    city = City(**city_info)
    city.save()
    return city
