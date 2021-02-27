from datetime import datetime

from apps.bot.APIs.TimezoneDBAPI import TimezoneDBAPI
from apps.bot.APIs.YandexGeoAPI import YandexGeoAPI
from apps.bot.classes.Consts import Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_attachments_from_attachments_or_fwd
from apps.service.models import City, TimeZone


class Profile(CommonCommand):
    names = ["профиль"]
    help_text = "Профиль - позволяет управлять вашим профилем"
    detail_help_text = "Профиль - присылает информацию по вашему профилю.\n" \
                       "Профиль город (название города) - устанавливает новый город\n" \
                       "Профиль город добавить (название города) - добавляет новый город в базу\n" \
                       "Профиль др (дата) - устанавливает новый др\n" \
                       "Профиль никнейм (никнейм) - устанавливает новый никнейм\n" \
                       "Профиль пол (мужской/женский) - устанавливает новый пол\n" \
                       "Профиль аватар - обновляет аватар из ВК\n" \
                       "Профиль аватар (изображение) - обновляет аватар из вложения\n"

    def start(self):
        if self.event.args:
            arg0 = self.event.args[0].lower()
        else:
            arg0 = None

        menu = [
            [["город"], self.menu_city],
            [["др"], self.menu_bd],
            [['ник', 'никнейм'], self.menu_nickname],
            [['пол'], self.menu_gender],
            [['аватар'], self.menu_avatar],
            [['default'], self.menu_default],
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    def menu_city(self):
        self.check_args(2)
        arg1 = self.event.args[1]
        if arg1 == 'добавить':
            city_name = " ".join(self.event.args[2:])
            city = add_city_to_db(city_name)
            return f"Добавил новый город - {city.name}"
        else:
            city_name = " ".join(self.event.args[1:])
            city = City.objects.filter(synonyms__icontains=city_name).first()
            if not city:
                raise PWarning("Не нашёл такого города. /профиль город добавить (название)")
            self.event.sender.city = city
            self.event.sender.save()
            return f"Изменил город на {self.event.sender.city.name}"

    def menu_bd(self):
        self.check_args(2)
        birthday = self.event.args[1]
        date_time_obj = datetime.strptime(birthday, '%d.%m.%Y')
        self.event.sender.birthday = date_time_obj.date()
        self.event.sender.save()
        return f"Изменил дату рождения на {self.event.sender.birthday.strftime('%d.%m.%Y')}"

    def menu_nickname(self):
        self.check_args(2)
        nickname = " ".join(self.event.args[1:])
        self.event.sender.nickname_real = nickname
        self.event.sender.save()
        return f"Изменил никнейм на {self.event.sender.nickname_real}"

    def menu_gender(self):
        self.check_args(2)
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

    def menu_avatar(self):
        images = get_attachments_from_attachments_or_fwd(self.event, 'photo')
        if len(images) > 0:
            self.event.sender.set_avatar(images[0]['private_download_url'])
        else:
            if self.event.platform != Platform.VK:
                raise PWarning("Обновление аватара по пользователю доступно только для ВК")
            self.bot.update_avatar(self.event.sender.user_id)
        return "Изменил аватарку"

    def menu_default(self):
        user = self.event.sender
        _city = user.city or "Не установлено"
        _bd = user.birthday
        if _bd:
            _bd = _bd.strftime('%d.%m.%Y')
        else:
            _bd = "Не установлено"
        _nickname = user.nickname_real or "Не установлено"
        msg = {
            'msg': f"Город - {_city}\n"
                   f"Дата рождения - {_bd}\n"
                   f"Никнейм - {_nickname}\n"
                   f"Пол - {user.get_gender_display()}"
        }
        if user.avatar:
            msg['attachments'] = self.bot.upload_photos(user.avatar.path)
        return msg


def add_city_to_db(city_name):
    yandexgeo_api = YandexGeoAPI()
    city_info = yandexgeo_api.get_city_info_by_name(city_name)
    if not city_info:
        raise PWarning("Не смог найти координаты для города")
    city_info['name'] = city_info['name'].replace('ё', 'е')
    city = City.objects.filter(name=city_info['name'])
    if len(city) != 0:
        return city.first()
        # raise PWarning("Такой город уже есть")
    city_info['synonyms'] = city_info['name'].lower()
    timezonedb_api = TimezoneDBAPI()
    timezone_name = timezonedb_api.get_timezone_by_coordinates(city_info['lat'], city_info['lon'])
    if not timezone_name:
        raise PWarning("Не смог найти таймзону для города")
    timezone_obj, _ = TimeZone.objects.get_or_create(name=timezone_name)

    city_info['timezone'] = timezone_obj
    city = City(**city_info)
    city.save()
    return city
