from datetime import datetime

from apps.bot.APIs.TimezoneDBAPI import TimezoneDBAPI
from apps.bot.APIs.YandexGeoAPI import YandexGeoAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.service.models import City, TimeZone


class Profile(Command):
    name = "профиль"
    name_tg = "profile"
    help_text = "позволяет управлять вашим профилем"
    help_texts = [
        "- присылает информацию по вашему профилю",
        "(имя, фамилия, логин/id, никнейм) - присылает информацию по профилю человека в конфе",
        "город (название города) - устанавливает новый город",
        "город добавить (название города) - добавляет новый город в базу",
        "др (дата) - устанавливает новый др",
        "имя (имя) - устанавливает новое имя",
        "фамилия (фамилия) - устанавливает новую фамилию",
        "никнейм (никнейм) - устанавливает новый никнейм",
        "пол (мужской/женский) - устанавливает новый пол",
        "аватар - обновляет аватар",
        "аватар (изображение) - обновляет аватар из вложения",
    ]

    def start(self):
        if self.event.message.args:
            arg0 = self.event.message.args[0]
        else:
            arg0 = None

        menu = [
            [["город"], self.menu_city],
            [["др", "дата"], self.menu_bd],
            [['ник', 'никнейм'], self.menu_nickname],
            [['имя'], self.menu_name],
            [['фамилия'], self.menu_surname],
            [['пол'], self.menu_gender],
            [['аватар'], self.menu_avatar],
            [['default'], self.menu_default],
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    def menu_city(self):
        self.check_args(2)
        arg1 = self.event.message.args_case[1]
        if arg1 == 'добавить':
            city_name = " ".join(self.event.message.args_case[2:])
            city = add_city_to_db(city_name)
            return f"Добавил новый город - {city.name}"
        else:
            city_name = " ".join(self.event.message.args_case[1:])
            city = City.objects.filter(synonyms__icontains=city_name).first()
            if not city:
                raise PWarning("Не нашёл такого города. /профиль город добавить (название)")
            self.event.sender.city = city
            self.event.sender.save()
            return f"Изменил город на {self.event.sender.city.name}"

    def menu_bd(self):
        self.check_args(2)
        birthday = self.event.message.args[1]

        show_birthday_year = True
        if birthday.count(".") == 1:
            birthday += ".1900"
            show_birthday_year = False
        try:
            date_time_obj = datetime.strptime(birthday, '%d.%m.%Y')
        except ValueError:
            raise PWarning("Не смог распарсить дату. Формат ДД.ММ.ГГГГ")

        self.event.sender.birthday = date_time_obj.date()
        self.event.sender.show_birthday_year = show_birthday_year
        self.event.sender.save()

        new_bday = self.event.sender.birthday.strftime(
            '%d.%m.%Y') if show_birthday_year else self.event.sender.birthday.strftime('%d.%m')
        return f"Изменил дату рождения на {new_bday}"

    def menu_nickname(self):
        self.check_args(2)
        nickname = " ".join(self.event.message.args_case[1:])
        self.event.sender.nickname_real = nickname
        self.event.sender.save()
        return f"Изменил никнейм на {self.event.sender.nickname_real}"

    def menu_name(self):
        self.check_args(2)
        name = " ".join(self.event.message.args_case[1:])
        self.event.sender.name = name
        self.event.sender.save()
        return f"Изменил имя на {self.event.sender.name}"

    def menu_surname(self):
        self.check_args(2)
        surname = " ".join(self.event.message.args_case[1:])
        self.event.sender.surname = surname
        self.event.sender.save()
        return f"Изменил фамилию на {self.event.sender.surname}"

    def menu_gender(self):
        self.check_args(2)
        gender = self.event.message.args[1]
        if gender in ['мужской', 'м', 'муж']:
            gender_code = self.event.sender.GENDER_MALE
        elif gender in ['женский', 'ж', 'жен']:
            gender_code = self.event.sender.GENDER_FEMALE
        else:
            gender_code = self.event.sender.GENDER_NONE
        self.event.sender.gender = gender_code
        self.event.sender.save()
        return f"Изменил пол на {self.event.sender.get_gender_display()}"

    def menu_avatar(self):
        images = self.event.get_all_attachments(PhotoAttachment)
        if len(images) > 0:
            self.event.sender.set_avatar(images[0].get_download_url())
        else:
            if self.event.platform not in [Platform.TG]:
                raise PWarning("Обновление аватара по пользователю доступно только для ВК/ТГ")
            self.bot.update_profile_avatar(self.event.sender, self.event.user.user_id)
        return "Изменил аватарку"

    def menu_default(self):
        if self.event.message.args:
            self.check_conversation()
            user = self.bot.get_profile_by_name(self.event.message.args, filter_chat=self.event.chat)
            return self.get_user_profile(user)
        user = self.event.sender
        return self.get_user_profile(user)

    def get_user_profile(self, user):
        _city = user.city or "Не установлено"
        _bd = user.birthday
        if user.celebrate_bday:
            if _bd:
                if not user.show_birthday_year:
                    _bd = _bd.strftime('%d.%m')
                else:
                    _bd = _bd.strftime('%d.%m.%Y')
            else:
                _bd = "Не установлено"
        else:
            _bd = "Скрыто"
        _nickname = user.nickname_real or "Не установлено"
        _name = user.name or "Не установлено"
        _surname = user.surname or "Не установлено"
        msg = {
            'text':
                f"Имя - {_name}\n"
                f"Фамилия - {_surname}\n"
                f"Никнейм - {_nickname}\n"
                f"Дата рождения - {_bd}\n"
                f"Город - {_city}\n"
                f"Пол - {user.get_gender_display()}"
        }
        if user.avatar:
            msg['attachments'] = self.bot.get_photo_attachment(user.avatar.path, peer_id=self.event.peer_id,
                                                               filename="petrovich_user_avatar.png")
        return msg


def add_city_to_db(city_name):
    city_name = city_name.capitalize()
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
