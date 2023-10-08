from datetime import datetime

from django.db import IntegrityError
from django.db.models import QuerySet, Q

from apps.bot.classes.command import Command
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import localize_datetime
from apps.service.models import Promocode as PromocodeModel
from petrovich.settings import DEFAULT_TIME_ZONE


class Promocode(Command):
    name = "промокод"
    names = ["промокоды", "промик", "промики", "пром", "промы"]
    help_text = "промокоды различных сервисов"
    help_texts = [
        "- список промокодов",
        "(название сервиса) - список промокодов по сервису",
        "добавить (название сервиса) (промокод) [срок действия=бессрочно] [описание] - добавляет промокод",
        "удалить (название сервиса) (промокод) - удаляет промокод",
        "удалить (промокод) - удаляет промокод"
    ]
    help_texts_extra = "Срок действия в добавлении промокода указывается в формате ДД.ММ.ГГГГ\n" \
                       "Если промокод добавлен в ЛС - он считается личным и будет выводиться только в лс\n" \
                       "Если промокод добавлен в чате - он считается публичным и будет выводиться во всех чатах"

    def start(self) -> ResponseMessage:
        if not self.event.message.args:
            answer = self.menu_all()
        else:
            arg0 = self.event.message.args[0]
            menu = [
                [['добавить'], self.menu_add],
                [['удалить'], self.menu_remove],
                [['default'], self.menu_search],
            ]
            method = self.handle_menu(menu, arg0)
            answer = method()
        return ResponseMessage(answer)

    def menu_all(self) -> ResponseMessageItem:
        promocodes = self._get_filtered_promocodes()

        if len(promocodes) == 0:
            raise PWarning("Пока что в базе нет промокодов")
        promocodes_str = self._get_promocodes_str(promocodes)
        return ResponseMessageItem(promocodes_str)

    def menu_add(self) -> ResponseMessageItem:
        self.check_args(3)
        args = self.event.message.args_case[1:]
        name = args[0].lower()
        code = args[1]

        try:
            PromocodeModel.objects.get(name=name, code=code)
            raise PWarning("Промокод с таким кодом и названием уже есть в базе")
        except PromocodeModel.DoesNotExist:
            pass

        description = ""
        expiration = None
        if len(args) > 2:
            try:
                expiration = datetime.strptime(args[2], '%d.%m.%Y').date()

                tz = self.event.sender.city.timezone.name if self.event.sender.city else DEFAULT_TIME_ZONE
                dt = localize_datetime(datetime.today(), tz).date()
                if dt > expiration:
                    raise PWarning("Промокод уже просрочен")

                description = " ".join(args[3:])
            except ValueError:
                description = " ".join(args[2:])
        try:
            PromocodeModel.objects.create(
                name=name,
                code=code,
                author=self.event.sender,
                is_personal=not self.event.chat,
                expiration=expiration,
                description=description,
            )
        except IntegrityError:
            raise PWarning("Промокод с таким кодом и названием уже есть в базе")

        return ResponseMessageItem("Промокод добавлен")

    def menu_remove(self) -> ResponseMessageItem:
        self.check_args(2)
        data = {
            "code": self.event.message.args_case[1]
        }
        if len(self.event.message.args) > 2:
            data['name'] = data['code'].lower()
            data['code'] = self.event.message.args_case[2]

        try:
            promocode = PromocodeModel.objects.get(**data)
        except PromocodeModel.DoesNotExist:
            return ResponseMessageItem("Промокод не найден")
        except PromocodeModel.MultipleObjectsReturned:
            if not data['name']:
                raise PWarning("Под запрос подходят два и более промокода. Уточните название сервиса")
            raise PWarning("Под запрос подходят два и более промокода")

        promocode.delete()

        return ResponseMessageItem("Промокод удалён")

    def menu_search(self) -> ResponseMessageItem:
        promocodes = self._get_filtered_promocodes()
        promocodes = promocodes.filter(name=self.event.message.args[0])
        if len(promocodes) == 0:
            raise PWarning("Не нашёл промокодов по этому названию")
        result = self._get_promocodes_str(promocodes)
        return ResponseMessageItem(result)

    def _get_promocodes_str(self, promocodes: QuerySet[PromocodeModel]) -> str:
        promocodes_list = [self._get_promocode_str(x) for x in promocodes]
        return "\n\n".join(promocodes_list)

    def _get_promocode_str(self, promocode: PromocodeModel) -> str:
        result = [
            f"{self.bot.get_underline_text(promocode.name.capitalize())}",
            f"{self.bot.get_formatted_text_line(promocode.code)}"
        ]

        if promocode.expiration:
            result.append(f"{promocode.expiration.strftime('%d.%m.%Y')}")
        if promocode.description:
            result.append(f"{promocode.description}")

        return "\n".join(result)

    def _get_filtered_promocodes(self) -> QuerySet:
        if self.event.chat:
            return PromocodeModel.objects.filter(is_personal=False)
        else:
            return PromocodeModel.objects.exclude(~Q(author=self.event.sender), is_personal=True)
