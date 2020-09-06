from datetime import datetime

from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.service.models import City


class Profile(CommonCommand):
    def __init__(self):
        names = ["профиль"]
        help_text = "Профиль - позволяет управлять вашим профилем"
        detail_help_text = "Профиль - присылает информацию по вашему профилю.\n" \
                           "Профиль город (название города) - устанавливает новый город\n" \
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
        city_name = " ".join(self.event.args[1:])
        city = City.objects.filter(synonyms__icontains=city_name).first()
        if not city:
            raise RuntimeWarning("Не нашёл такого города. /город добавить (название)")
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
