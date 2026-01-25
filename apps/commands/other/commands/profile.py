from datetime import datetime

from apps.bot.consts import PlatformEnum, RoleEnum
from apps.bot.core.bot.tg_bot.tg_bot import TgBot
from apps.bot.core.messages.attachments.photo import PhotoAttachment
from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.models import Profile as ProfileModel
from apps.bot.utils import get_profile_by_name
from apps.commands.command import Command
from apps.commands.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.shared.exceptions import PWarning
from apps.shared.models import City


class Profile(Command):
    name = "профиль"

    help_text = HelpText(
        commands_text="позволяет управлять вашим профилем",
        help_texts=[
            HelpTextItem(RoleEnum.USER, [
                HelpTextArgument(None, "присылает информацию по вашему профилю"),
                HelpTextArgument(
                    "(имя, фамилия, логин/id, никнейм)",
                    "присылает информацию по профилю человека в конфе"),
                HelpTextArgument("город (название города)", "устанавливает новый город"),
                HelpTextArgument("город добавить (название города)", "добавляет новый город в базу"),
                HelpTextArgument("др (дата)", "устанавливает новый др"),
                HelpTextArgument("имя (имя)", "устанавливает новое имя"),
                HelpTextArgument("фамилия (фамилия)", "устанавливает новую фамилию"),
                HelpTextArgument("никнейм (никнейм)", "устанавливает новый никнейм"),
                HelpTextArgument("пол (мужской/женский)", "устанавливает новый пол"),
                HelpTextArgument("аватар", "обновляет аватар"),
                HelpTextArgument("аватар (изображение)", "обновляет аватар из вложения")
            ])
        ]
    )

    platforms = [PlatformEnum.TG]

    bot: TgBot

    def start(self) -> ResponseMessage:
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
        rmi = method()
        return ResponseMessage(rmi)

    def menu_city(self) -> ResponseMessageItem:
        self.check_args(2)
        city_name = " ".join(self.event.message.args_case[1:])
        city = City.objects.filter(synonyms__icontains=city_name).first()
        if not city:
            raise PWarning(
                "Не нашёл такого города.\n"
                f"Попросите админа добавить ваш город"
            )
        self.event.sender.city = city
        self.event.sender.save()
        answer = f"Изменил город на {self.event.sender.city.name}"
        return ResponseMessageItem(text=answer)

    def menu_bd(self) -> ResponseMessageItem:
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
        self.event.sender.settings.show_birthday_year = show_birthday_year
        self.event.sender.save()

        new_bday = self.event.sender.birthday.strftime(
            '%d.%m.%Y') if show_birthday_year else self.event.sender.birthday.strftime('%d.%m')
        answer = f"Изменил дату рождения на {new_bday}"
        return ResponseMessageItem(text=answer)

    def menu_nickname(self) -> ResponseMessageItem:
        self.check_args(2)
        nickname = " ".join(self.event.message.args_case[1:])
        self.event.sender.nickname_real = nickname
        self.event.sender.save()
        answer = f"Изменил никнейм на {self.event.sender.nickname_real}"
        return ResponseMessageItem(text=answer)

    def menu_name(self) -> ResponseMessageItem:
        self.check_args(2)
        name = " ".join(self.event.message.args_case[1:])
        self.event.sender.name = name
        self.event.sender.save()
        answer = f"Изменил имя на {self.event.sender.name}"

        return ResponseMessageItem(text=answer)

    def menu_surname(self) -> ResponseMessageItem:
        self.check_args(2)
        surname = " ".join(self.event.message.args_case[1:])
        self.event.sender.surname = surname
        self.event.sender.save()
        answer = f"Изменил фамилию на {self.event.sender.surname}"
        return ResponseMessageItem(text=answer)

    def menu_gender(self) -> ResponseMessageItem:
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
        answer = f"Изменил пол на {self.event.sender.get_gender_display()}"
        return ResponseMessageItem(text=answer)

    def menu_avatar(self) -> ResponseMessageItem:
        images = self.event.get_all_attachments([PhotoAttachment])
        if len(images) > 0:
            avatar = images[0]
        else:
            if self.event.platform not in [PlatformEnum.TG]:
                raise PWarning("Обновление аватара по пользователю доступно только для ТГ")
            avatar = self._get_photo_from_tg()
        self.event.sender.set_avatar(avatar)
        answer = "Изменил аватарку"
        return ResponseMessageItem(text=answer)

    def _get_photo_from_tg(self):
        profile_photos = self.bot.get_user_profile_photos(self.event.user.user_id)
        if len(profile_photos) == 0:
            raise PWarning("Нет фотографий в профиле")

        pa = PhotoAttachment()
        pa.parse_tg(profile_photos[0][-1])
        return pa

    def menu_default(self) -> ResponseMessageItem:
        if self.event.message.args:
            self.check_conversation()
            profile = get_profile_by_name(self.event.message.args, filter_chat=self.event.chat)
            return self.get_profile_info(profile)
        profile = self.event.sender
        return self.get_profile_info(profile)

    def get_profile_info(self, profile: ProfileModel) -> ResponseMessageItem:
        not_defined = "Не установлено"

        _city = profile.city or not_defined
        _bd = profile.birthday
        if profile.settings.celebrate_bday:
            if _bd:
                if not profile.settings.show_birthday_year:
                    _bd = _bd.strftime('%d.%m')
                else:
                    _bd = _bd.strftime('%d.%m.%Y')
            else:
                _bd = not_defined
        else:
            _bd = "Скрыто"
        _nickname = profile.nickname_real or not_defined
        _name = profile.name or not_defined
        _surname = profile.surname or not_defined

        roles = []
        for role in profile.roles.all():
            roles.append(RoleEnum[role.name])  # noqa
        roles = sorted(roles)
        roles_str = ", ".join(roles)

        answer = \
            f"Имя: {_name}\n" \
            f"Фамилия: {_surname}\n" \
            f"Никнейм: {_nickname}\n" \
            f"Дата рождения: {_bd}\n" \
            f"Город: {_city}\n" \
            f"Пол: {profile.get_gender_display().capitalize()}\n\n" \
            f"Роли: {roles_str}"
        rmi = ResponseMessageItem(text=answer)

        if profile.avatar:
            attachment = self.bot.get_photo_attachment(
                path=profile.avatar.path,
                peer_id=self.event.peer_id,
                filename="petrovich_user_avatar.png"
            )
            rmi.attachments = [attachment]

        return rmi
